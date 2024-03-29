import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from athens_graphops.designer import Designer, Instance
from athens_graphops.query import Client


class Assignment(BaseModel):
    name: str
    value: str


class JSONInstance(BaseModel):
    model: str
    name: str
    assignment: List[Assignment]

    def to_dict(self):
        dict_obj = {"assignment": {}}
        for assign in self.assignment:
            dict_obj["assignment"][assign.name] = assign.value

        dict_obj["model"] = self.model
        dict_obj["name"] = self.name

        return dict_obj


class Parameter(BaseModel):
    name: str
    value: Any


class IntParameter(Parameter):
    value: int


class FloatParameter(Parameter):
    value = float


class StringParameter(Parameter):
    value = str


class Connection(BaseModel):
    connector1: str
    connector2: str
    instance1: JSONInstance
    instance2: JSONInstance

    def to_dict(self):
        dict_obj = self.dict(exclude={"instance1", "instance2"})
        dict_obj["instance1"] = self.instance1.name
        dict_obj["instance2"] = self.instance2.name

        return dict_obj


class JSONUAVDesign(BaseModel):
    parameters: List[Parameter]
    design: str = Field(...)

    instances: List[JSONInstance]
    connections: List[Connection]

    @classmethod
    def from_json_file(cls, loc):
        with open(loc, "rb") as json_file:
            design_dict = json.load(json_file)[0]
            return cls.from_dict(design_dict)

    @classmethod
    def from_dict(cls, design_dict):
        instances = []
        parameters = []
        connections = []
        instance_cache = {}
        design = design_dict["design"]
        for instance_dict in design_dict.get("instances", []):
            assignments = []
            for name, value in instance_dict["assignment"].items():
                assignments.append(Assignment(name=name, value=value))
            instance_model = instance_dict["model"]
            instance_name = instance_dict["name"]
            instance = JSONInstance(
                assignments=assignments,
                name=instance_name,
                model=instance_model,
                assignment=assignments,
            )
            instance_cache[instance.name] = instance
            instances.append(instance)

        for name, value in design_dict.get("parameters", {}).items():
            if "naca" in name.lower():
                param = StringParameter(name=name, value=value)
            else:
                try:
                    value = int(value)
                    param = FloatParameter(name=name, value=value)
                except ValueError:
                    try:
                        value = float(value)
                        param = FloatParameter(name=name, value=value)
                    except ValueError:
                        param = StringParameter(name=name, value=value)
            parameters.append(param)

        for connection_dict in design_dict.get("connections", []):
            conn = Connection(
                connector1=connection_dict["connector1"],
                connector2=connection_dict["connector2"],
                instance1=instance_cache[connection_dict["instance1"]],
                instance2=instance_cache[connection_dict["instance2"]],
            )
            connections.append(conn)

        return cls(
            design=design,
            connections=connections,
            instances=instances,
            parameters=parameters,
        )

    def to_dict(self):
        dict_obj = {
            "connections": list(
                connection.to_dict() for connection in self.connections
            ),
            "design": self.design,
            "instances": list(instance.to_dict() for instance in self.instances),
            "parameters": {},
        }
        for param in self.parameters:
            dict_obj["parameters"][param.name] = str(param.value)
        return dict_obj

    def get_parameter_for(self, assignment: Assignment):
        for param in self.parameters:
            if param.name == assignment.value:
                return param

    def _update_instance_parameters(
        self,
        designer: Designer,
        inst: Instance,
        assignments: List[Assignment],
        cache: set,
    ) -> None:
        for assign in assignments:
            param = self.get_parameter_for(assign)
            if param:
                designer.set_named_parameter(
                    [inst],
                    param.name,
                    assign.name,
                    param.value,
                    param_exist=param.name in cache,
                )
                cache.add(param.name)
                print(
                    f"{assign.name} has been assigned global design parameter {assign.value}, whose value is {param.value}"
                )

    def _add_instance(
        self,
        designer: Designer,
        instance: JSONInstance,
        instance_cache: Dict,
        param_cache: set,
    ):
        name = instance.name
        model = instance.model
        assignments = instance.assignment
        if name not in instance_cache:
            inst = designer.add_instance(model, name)
            instance_cache[name] = inst
            self._update_instance_parameters(designer, inst, assignments, param_cache)

    def instantiate(
        self,
        new_name: Optional[str] = None,
        overwrite=False,
    ) -> None:
        graph_guid = new_name if new_name is not None else self.design
        client = Client()
        all_design_names = set(client.get_design_names())  # Assume Unique Design Names

        if overwrite and (graph_guid in all_design_names):
            print(f"Deleting existing design {graph_guid}")
            client.delete_design(graph_guid)
            all_design_names.discard(graph_guid)

        client.close()

        if graph_guid in all_design_names:
            raise ValueError(f"A design with name {new_name} already exists")

        designer = Designer()
        designer.create_design(graph_guid)
        instance_cache = {}
        connection_cache = set()
        param_cache = set()

        for connection in self.connections:
            self._add_instance(
                designer, connection.instance1, instance_cache, param_cache
            )
            self._add_instance(
                designer, connection.instance2, instance_cache, param_cache
            )

            inst1 = instance_cache[connection.instance1.name]
            inst2 = instance_cache[connection.instance2.name]

            conn_id = (
                (inst1.name, connection.connector1),
                (inst2.name, connection.connector2),
            )

            if conn_id not in connection_cache:
                designer.connect(
                    inst1, connection.connector1, inst2, connection.connector2
                )

            connection_cache.add(conn_id)
            connection_cache.add(tuple(reversed(conn_id)))

        for parameter in self.parameters:
            if parameter.name not in param_cache:
                designer.set_config_param(parameter.name, parameter.value)
                print(
                    f"Created unused global parameter {parameter.name} whose value is {parameter.value}"
                )

        designer.client.close()
        designer.client = None


def run(args=None):
    from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

    parser = ArgumentParser(
        "JSON Designer", formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-f",
        "--json-file",
        required=True,
        type=str,
        help="The json file to create the design from",
    )
    parser.add_argument(
        "-o",
        "--overwrite",
        required=False,
        action="store_true",
        default=False,
        help="If true overwrite the existing design",
    )
    parser.add_argument(
        "-n", "--new-name", required=False, type=str, help="New name for the design"
    )

    args = parser.parse_args(args)

    designer = JSONUAVDesign.from_json_file(args.json_file)
    designer.instantiate(args.new_name, args.overwrite)
