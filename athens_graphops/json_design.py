import json
from typing import Any, List, Optional

from pydantic import BaseModel, Field
from athens_graphops.designer import Designer, Instance
from athens_graphops.query import Client
from athens_graphops.dataset import get_model_data


class Assignment(BaseModel):
    name: str
    value: str


class JSONInstance(BaseModel):
    model: str
    name: str
    assignment: List[Assignment]

    def to_dict(self):
        dict_obj = {
            "assignment": {}
        }
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
        dict_obj = self.dict(exclude={'instance1', 'instance2'})
        dict_obj['instance1'] = self.instance1.name
        dict_obj['instance2'] = self.instance2.name

        return dict_obj


class JSONUAVDesign(BaseModel):
    parameters: List[Parameter]
    design: str = Field(
        ...
    )

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
                assignments.append(
                    Assignment(
                        name=name,
                        value=value
                    )
                )
            instance_model = instance_dict["model"]
            instance_name = instance_dict["name"]
            instance = JSONInstance(
                assignments=assignments,
                name=instance_name,
                model=instance_model,
                assignment=assignments
            )
            instance_cache[instance.name] = instance
            instances.append(instance)

        for name, value in design_dict.get("parameters", {}).items():
            if "naca" in name.lower():
                param = StringParameter(
                    name=name,
                    value=value
                )
            else:
                try:
                    value = int(value)
                    param = FloatParameter(
                        name=name,
                        value=value
                    )
                except ValueError:
                    try:
                        value = float(value)
                        param = FloatParameter(
                            name=name,
                            value=value
                        )
                    except ValueError:
                        param = StringParameter(
                            name=name,
                            value=value
                        )
            parameters.append(param)

        for connection_dict in design_dict.get("connections", []):
            conn = Connection(
                connector1=connection_dict["connector1"],
                connector2=connection_dict["connector2"],
                instance1=instance_cache[connection_dict["instance1"]],
                instance2=instance_cache[connection_dict["instance2"]]
            )
            connections.append(conn)

        return cls(
            design=design,
            connections=connections,
            instances=instances,
            parameters=parameters,
        )

    def to_dict(self):
        dict_obj = {"connections": list(connection.to_dict() for connection in self.connections), "design": self.design,
                    "instances": list(instance.to_dict() for instance in self.instances), "parameters": {}}
        for param in self.parameters:
            dict_obj["parameters"][param.name] = str(param.value)
        return dict_obj

    def get_value_for(self, assignment: Assignment):
        for param in self.parameters:
            if param.name == assignment.value:
                return param.value

    def update_instance_parameters(self, designer: Designer, inst: Instance, assignments: List[Assignment]) -> None:
        for assign in assignments:
            value = self.get_value_for(assign)
            if value:
                designer.set_parameter(
                    inst,
                    assign.name,
                    value
                )
                print(
                    f"{assign.name} has been assigned global design parameter {assign.value}, whose value is {self.get_value_for(assign)}"
                )

    def _add_instance(self, designer:Designer, instance: JSONInstance, cache):
        name = instance.name
        model = instance.model
        assignments = instance.assignment
        if name not in cache:
            inst = designer.add_instance(model, name)
            print(f"Created instance for model {model} as {name}")
            cache[name] = inst
            self.update_instance_parameters(designer, inst, assignments)
        else:
            print(f"Found existing instance {name}")

    def instantiate(self,
                    new_name: Optional[str] = None,
                    host: Optional[str] = None,
                    timeout: Optional[int] = None,
                    overwrite=False) -> None:
        graph_guid = new_name or self.design
        client = Client(host=host or "localhost", timeout=timeout or 120000)
        all_design_names = client.get_design_names()

        if overwrite and (graph_guid in all_design_names):
            print("Deleting existing design")
            client.delete_design(graph_guid)
            client.close()
        elif graph_guid in all_design_names:
            raise ValueError(
                f"A design with name {new_name} already exists"
            )
        designer = Designer()
        designer.create_design(new_name)
        created_instances = {}
        for connection in self.connections:
            self._add_instance(designer, connection.instance1, created_instances)
            self._add_instance(designer, connection.instance2, created_instances)

            inst1 = created_instances[connection.instance1.name]
            inst2 = created_instances[connection.instance2.name]
            designer.connect(
                inst1,
                connection.connector1,
                inst2,
                connection.connector2
            )
            print(f"Connected {connection.connector1} of {inst1.name} to {connection.connector2} of {inst2.name}")

        # designer.close_design(corpus="uav")
        designer.client.close()


if __name__ == "__main__":
    design = JSONUAVDesign.from_json_file("designs/NewAxe_Cargo.json")
    design.instantiate('NewAxe_Cargo2', overwrite=True)
