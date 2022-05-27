#!/usr/bin/env python3
# Copyright (C) 2022, Miklos Maroti
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from typing import Optional, Tuple, Union

from .query import Client
from .dataset import get_model_data


class Instance():
    def __init__(self, model: str, name: str):
        self.model = model
        self.name = name
        self.parameters = dict()


class Designer():
    def __init__(self):
        self.client = None

    def create_design(self, design: str):
        assert self.client is None
        self.client = Client()
        self.instances = dict()
        self.nextid = 1

        self.design = design
        print("Creating design", self.design)
        self.client.create_design(self.design)

        self.fuselage = None

    def get_name(self) -> str:
        instance = "inst_{:04}".format(self.nextid)
        self.nextid += 1
        return instance

    def add_instance(self, model: str, name: Optional[str]) -> str:
        assert name is None or isinstance(name, str)
        if not name:
            name = self.get_name()

        assert name not in self.instances

        data = get_model_data(model)
        assert data

        instance = Instance(model, name)
        self.instances[name] = instance

        print("Creating", model, name)
        self.client.create_instance(self.design, model, name)

        return instance

    def connect(self, instance1: Instance, connector1: str,
                instance2: Instance, connector2: str):
        assert isinstance(instance1, Instance) and isinstance(
            instance2, Instance)

        print("Creating connection from", instance1.name, connector1,
              "to", instance2.name, connector2)
        self.client.create_connection(
            self.design, instance1.name, connector1, instance2.name, connector2)

    def set_parameter(self, instance: Instance, param: str, value: Union[float, str]):
        assert isinstance(instance, Instance)

        full_name = instance.name + "_" + param
        self.client.create_parameter(self.design, full_name, value)
        self.client.assign_parameter(
            self.design, instance.name, param, full_name)

    def set_config_param(self, param: str, value: Union[float, str]):
        self.client.create_parameter(self.design, param, value)

    def add_fuselage(self,
                     length: float,
                     sphere_diameter: float,
                     middle_length: float,
                     tail_diameter: float,
                     floor_height: float,
                     seat_1_fb: float,
                     seat_1_lr: float,
                     seat_2_fb: float,
                     seat_2_lr: float,
                     port_thickness: float = 100,
                     top_port_disp: float = 0,
                     bottom_port_disp: float = 0,
                     left_port_disp: float = 0,
                     right_port_disp: float = 0,
                     name: Optional[str] = None):
        assert self.fuselage is None

        instance = self.add_instance("FUSE_SPHERE_CYL_CONE", name)
        self.set_parameter(instance, "LENGTH", length)
        self.set_parameter(instance, "SPHERE_DIAMETER", sphere_diameter)
        self.set_parameter(instance, "MIDDLE_LENGTH", middle_length)
        self.set_parameter(instance, "TAIL_DIAMETER", tail_diameter)
        self.set_parameter(instance, "FLOOR_HEIGHT", floor_height)
        self.set_parameter(instance, "SEAT_1_FB", seat_1_fb)
        self.set_parameter(instance, "SEAT_1_LR", seat_1_lr)
        self.set_parameter(instance, "SEAT_2_FB", seat_2_fb)
        self.set_parameter(instance, "SEAT_2_LR", seat_2_lr)
        self.set_parameter(instance, "PORT_THICKNESS", port_thickness)
        self.set_parameter(instance, "TOP_PORT_DISP", top_port_disp)
        self.set_parameter(instance, "BOTTOM_PORT_DISP", bottom_port_disp)
        self.set_parameter(instance, "LEFT_PORT_DISP", left_port_disp)
        self.set_parameter(instance, "RIGHT_PORT_DISP", right_port_disp)

        self.fuselage = instance
        return instance

    def add_cylinder(self,
                     length: float,
                     diameter: float,
                     port_thickness: float,
                     front_angle: float = 0,
                     name: Optional[str] = None,
                     mount_inst: Optional[Instance] = None,
                     mount_conn: Optional[str] = None) -> str:
        # observed requirements in CREO, but min port_thickness is flaky
        assert 8 <= port_thickness < diameter <= length
        assert 0 <= front_angle <= 360

        instance = self.add_instance("PORTED_CYL", name)
        self.set_parameter(instance, "DIAMETER", diameter)
        self.set_parameter(instance, "LENGTH", length)
        self.set_parameter(instance, "PORT_THICKNESS", port_thickness)
        self.set_parameter(instance, "FRONT_ANGLE", front_angle)

        if mount_inst:
            self.connect(instance, "FRONT_CONNECTOR",
                         mount_inst, mount_conn)

        return instance

    def add_flip_in(self,
                    diameter: float,
                    name: Optional[str] = None):
        instance = self.add_instance("Cyl_Flip", name)
        self.set_parameter(instance, "DIAMETER", diameter)

        return instance

    def add_flip_out(self,
                     diameter: float,
                     name: Optional[str] = None,
                     front_inst: Optional[Instance] = None,
                     front_conn: Optional[str] = None,
                     rear_inst: Optional[Instance] = None,
                     rear_conn: Optional[str] = None):
        instance = self.add_instance("Cyl_Flip_Out", name)
        self.set_parameter(instance, "DIAMETER", diameter)

        if front_inst:
            self.connect(instance, "Flip_Connector_1",
                         front_inst, front_conn)
        if rear_inst:
            self.connect(instance, "Flip_Connector_2",
                         rear_inst, rear_conn)

        return instance

    def add_passenger(self, name: Optional[str] = None,
                      fuselage_inst: Optional[Instance] = None,
                      fuselage_conn: Optional[str] = None) -> str:
        instance = self.add_instance("Passenger", name)
        if fuselage_inst:
            self.connect(instance, "Connector",
                         fuselage_inst, fuselage_conn)
        return instance

    def add_battery_controller(self, name: Optional[str] = None) -> str:
        instance = self.add_instance("BatteryController", name)
        return instance

    def add_wing(self,
                 naca: str,
                 chord: float,
                 span: float,
                 load: float,
                 name: Optional[str] = None,
                 left_inst: Optional[Instance] = None,
                 left_conn: Optional[str] = None,
                 right_inst: Optional[Instance] = None,
                 right_conn: Optional[str] = None):
        assert len(naca) == 4 and chord >= 1 and span >= 1 and load >= 1
        thickness = int(naca[2:4])

        instance = self.add_instance("naca_wing", name)
        self.set_parameter(instance, "NACA_Profile", naca)
        self.set_parameter(instance, "THICKNESS", thickness)
        self.set_parameter(instance, "CHORD_1", chord)
        self.set_parameter(instance, "CHORD_2", chord)
        self.set_parameter(instance, "SPAN", span)
        self.set_parameter(instance, "LOAD", load)

        if left_inst:
            self.connect(instance, "Connector_1", left_inst, left_conn)

        if right_inst:
            self.connect(instance, "Connector_2", right_inst, right_conn)

        return instance

    def add_battery(self, model: str,
                    naca: str,
                    chord: float,
                    span: float,
                    mount_side: int,
                    voltage_request: float,
                    volume_percent: float,
                    name: Optional[str] = None,
                    wing_inst: Optional[Instance] = None,
                    controller_inst: Optional[Instance] = None):
        assert len(naca) == 4 and chord >= 1 and span >= 1
        assert mount_side in [1, 2] and 0 <= volume_percent <= 100
        thickness = int(naca[2:4])

        instance = self.add_instance(model, name)
        self.set_parameter(instance, "THICKNESS", thickness)
        self.set_parameter(instance, "CHORD_1", chord)
        self.set_parameter(instance, "CHORD_2", chord)
        self.set_parameter(instance, "SPAN", span)
        self.set_parameter(instance, "MOUNT_SIDE", mount_side)
        self.set_parameter(instance, "VOLTAGE_REQUEST", voltage_request)
        self.set_parameter(instance, "VOLUME_PERCENT", volume_percent)

        if wing_inst:
            if mount_side == 1:
                self.connect(instance, "Battery_Connector_1_out",
                             wing_inst, "Battery_Connector_1")
            else:
                self.connect(instance, "Battery_Connector_2_out",
                             wing_inst, "Battery_Connector_2")

        if controller_inst:
            self.connect(instance, "PowerBus",
                         controller_inst, "BatteryPower")

        return instance

    def add_motor(self, model: str,
                  name: Optional[str] = None,
                  mount_inst: Optional[Instance] = None,
                  mount_conn: Optional[str] = None,
                  controller_inst: Optional[Instance] = None):
        instance = self.add_instance(model, name)

        if mount_inst:
            self.connect(instance, "Base_Connector",
                         mount_inst, mount_conn)

        if controller_inst:
            self.connect(instance, "MotorPower",
                         controller_inst, "MotorPower")

        return instance

    def add_propeller(self, model: str,
                      prop_type: int,
                      direction: int,
                      name: Optional[str] = None,
                      motor_inst: Optional[Instance] = None):
        assert prop_type in [-1, 1] and direction in [-1, 1]

        instance = self.add_instance(model, name)
        self.set_parameter(instance, "Prop_type", prop_type)
        self.set_parameter(instance, "Direction", direction)

        if motor_inst:
            self.connect(motor_inst, "Prop_Connector",
                         instance, "MOTOR_CONNECTOR_CS_IN")

        return instance

    def add_motor_propeller(self,
                            motor_model: str,
                            prop_model: str,
                            prop_type: int,
                            direction: int,
                            name_prefix: Optional[str] = None,
                            mount_inst: Optional[Instance] = None,
                            mount_conn: Optional[str] = None,
                            controller_inst: Optional[Instance] = None):
        motor_inst = self.add_motor(
            model=motor_model,
            name=name_prefix + "_motor" if name_prefix else None,
            mount_inst=mount_inst,
            mount_conn=mount_conn,
            controller_inst=controller_inst)

        prop_inst = self.add_propeller(
            model=prop_model,
            name=name_prefix + "_prop" if name_prefix else None,
            prop_type=prop_type,
            direction=direction,
            motor_inst=motor_inst,
        )

        return motor_inst, prop_inst

    def close_design(self):
        assert self.fuselage is not None

        orient = self.add_instance("Orient", "Orient")
        self.connect(orient, "ORIENTCONN", self.fuselage, "ORIENT")
        self.client.orient_design(self.design, orient.name)

        print("Closing design", self.design)
        self.fuselage = None
        self.design = None

        self.client.close()
        self.client = None


def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    args = parser.parse_args(args)


if __name__ == '__main__':
    run()