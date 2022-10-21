from pydantic import BaseModel, Field

from typing import Any, List


class Assignment(BaseModel):
    name: str
    value: str


class Instance(BaseModel):
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
    instance1: Instance
    instance2: Instance

    def to_dict(self):
        dict_obj = self.dict(exclude={'instance1', 'instance2'})
        dict_obj['instance1'] = self.instance1.name
        dict_obj['instance2'] = self.instance2.name


        return dict_obj


class Design(BaseModel):
    parameters: List[Parameter]
    design: str = Field(
        ...
    )

    instances: List[Instance]
    connections: List[Connection]

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
            instance = Instance(
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
