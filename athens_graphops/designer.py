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

        self.fuselage = self.add_instance("FUSE_SPHERE_CYL_CONE", "fuselage")
        self.orient = self.add_instance("Orient", "Orient")
        self.connect(self.orient, "ORIENTCONN", self.fuselage, "ORIENT")
        return self.fuselage

    def get_name(self) -> str:
        instance = "inst_{:04}".format(self.nextid)
        self.nextid += 1
        return instance

    def add_instance(self, model: str, name: str) -> str:
        # TODO: switch instance/name throughout
        assert name not in self.instances
        self.instances[name] = {
            "name": name,
            "model": model,
        }
        print("Creating", model, name)
        self.client.create_instance(self.design, model, name)
        return name

    def connect(self, instance1: str, connector1: str,
                instance2: str, connector2: str):
        print("Creating connection from", instance1, connector1,
              "to", instance2, connector2)
        self.client.create_connection(
            self.design, instance1, connector1, instance2, connector2)

    def set_parameter(self, instance: str, name: str, value: Union[float, str]):
        param_name = instance + "_" + name
        self.client.create_parameter(self.design, param_name, value)
        self.client.assign_parameter(self.design, instance, name, param_name)

    def add_cylinder(self,
                     instance: str,
                     length: float,
                     diameter: float,
                     port_thickness: float,
                     mount_inst: Optional[str] = None,
                     mount_conn: Optional[str] = None) -> str:
        # observed requirements in CREO, but min port_thickness is flaky
        assert 8 <= port_thickness < diameter <= length

        instance = self.add_instance("PORTED_CYL", instance)
        self.set_parameter(instance, "DIAMETER", diameter)
        self.set_parameter(instance, "LENGTH", length)
        self.set_parameter(instance, "PORT_THICKNESS", port_thickness)

        if mount_inst:
            self.connect(instance, "FRONT_CONNECTOR",
                         mount_inst, mount_conn)

        return instance

    def add_passanger(self, instance: str,
                      fuselage_inst: Optional[str] = None,
                      fuselage_conn: Optional[str] = None) -> str:
        instance = self.add_instance("Passenger", instance)
        if fuselage_inst:
            self.connect(instance, "Connector",
                         fuselage_inst, fuselage_conn)
        return instance

    def add_battery_controller(self, instance: str) -> str:
        instance = self.add_instance("BatteryController", instance)
        return instance

    def add_wing(self,
                 instance: str,
                 naca: str,
                 chord: float,
                 span: float,
                 load: float):
        assert len(naca) == 4 and chord >= 1 and span >= 1 and load >= 1
        thickness = int(naca[2:4])

        instance = self.add_instance("naca_wing", instance)
        self.set_parameter(instance, "NACA_Profile", naca)
        self.set_parameter(instance, "THICKNESS", thickness)
        self.set_parameter(instance, "CHORD_1", chord)
        self.set_parameter(instance, "CHORD_2", chord)
        self.set_parameter(instance, "SPAN", span)
        self.set_parameter(instance, "LOAD", load)
        return instance

    def add_battery(self, model: str,
                    instance: str,
                    naca: str,
                    chord: float,
                    span: float,
                    mount_side: int,
                    voltage_request: float,
                    volume_percent: float,
                    wing_inst: Optional[str] = None,
                    controller_inst: Optional[str] = None):
        assert len(naca) == 4 and chord >= 1 and span >= 1
        assert mount_side in [1, 2] and 0 <= volume_percent <= 100
        thickness = int(naca[2:4])

        instance = self.add_instance(model, instance)
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
                  instance: str,
                  mount_inst: Optional[str] = None,
                  mount_conn: Optional[str] = None,
                  controller_inst: Optional[str] = None):
        instance = self.add_instance(model, instance)

        if mount_inst:
            self.connect(instance, "Base_Connector",
                         mount_inst, mount_conn)

        if controller_inst:
            self.connect(instance, "MotorPower",
                         controller_inst, "MotorPower")

        return instance

    def add_propeller(self, model: str,
                      instance: str,
                      prop_type: int,
                      direction: int,
                      motor_inst: Optional[str] = None):
        assert prop_type in [-1, 1] and direction in [-1, 1]

        instance = self.add_instance(model, instance)
        self.set_parameter(instance, "Prop_type", prop_type)
        self.set_parameter(instance, "Direction", direction)

        if motor_inst:
            self.connect(motor_inst, "Prop_Connector",
                         instance, "MOTOR_CONNECTOR_CS_IN")

        return instance

    def close_design(self):
        print("Closing design", self.design)
        self.client.orient_design(self.design, self.orient)
        self.client.close()
        self.client = None


def create_minimal():
    designer = Designer()
    designer.create_design("Minimal")
    designer.close_design()


def create_many_cylinders():
    designer = Designer()
    designer.create_design("ManyCylinders")

    previous = designer.fuselage
    for diameter in [10, 20, 30, 50, 100, 150, 200]:
        for port_thickness in [8, 15, 25, 40, 80, 150]:
            if not port_thickness < diameter:
                continue
            for length in [20, 30, 50, 100, 200, 300, 400, 500]:
                if not diameter <= length:
                    continue

                instance = designer.add_cylinder(
                    instance=designer.get_name(),
                    port_thickness=port_thickness,
                    diameter=diameter,
                    length=length)
                designer.connect(previous, "REAR_CONNECTOR", instance, "FRONT_CONNECTOR")
                previous = instance

    designer.close_design()


def create_tail_sitter():
    designer = Designer()
    fuselage = designer.create_design("TailSitter")

    designer.add_passanger("passenger1",
                           fuselage_inst=fuselage,
                           fuselage_conn="SEAT_1_CONNECTOR")
    designer.add_passanger("passenger2",
                           fuselage_inst=fuselage,
                           fuselage_conn="SEAT_2_CONNECTOR")

    wing_naca = "2418"
    wing_chord = 1000
    wing_span = 10000
    wing_load = 10000

    right_wing = designer.add_wing("right_wing",
                                   naca=wing_naca,
                                   chord=wing_chord,
                                   span=wing_span,
                                   load=wing_load)
    designer.connect(right_wing, "Connector_1", fuselage, "RIGHT_CONNECTOR")

    left_wing = designer.add_wing("left_wing",
                                  naca=wing_naca,
                                  chord=wing_chord,
                                  span=wing_span + 100,
                                  load=wing_load)
    designer.connect(left_wing, "Connector_2", fuselage, "LEFT_CONNECTOR")

    battery_controller = designer.add_battery_controller("battery_controller")
    battery_model = "VitalyBeta"
    battery_voltage = 800   # was 840
    battery_percent = 100

    designer.add_battery(battery_model,
                         "right_battery",
                         naca=wing_naca,
                         chord=wing_chord,
                         span=wing_span,
                         mount_side=1,
                         voltage_request=battery_voltage,
                         volume_percent=battery_percent,
                         wing_inst=right_wing,
                         controller_inst=battery_controller)

    designer.add_battery(battery_model,
                         "left_battery",
                         naca=wing_naca,
                         chord=wing_chord,
                         span=wing_span,
                         mount_side=2,
                         voltage_request=battery_voltage,
                         volume_percent=battery_percent,
                         wing_inst=left_wing,
                         controller_inst=battery_controller)

    cylinder_diameter = 100
    port_thickness = 0.75 * cylinder_diameter
    spacer_length = 600

    top_spacer = designer.add_cylinder("top_spacer",
                                       length=spacer_length,
                                       diameter=cylinder_diameter,
                                       port_thickness=port_thickness,
                                       mount_inst=fuselage,
                                       mount_conn="TOP_CONNECTOR")

    top_hub = designer.add_cylinder("top_hub",
                                    length=cylinder_diameter,
                                    diameter=cylinder_diameter,
                                    port_thickness=port_thickness,
                                    mount_inst=top_spacer,
                                    mount_conn="REAR_CONNECTOR")

    top_right_bar = designer.add_cylinder("top_right_bar",
                                          length=1600,
                                          diameter=cylinder_diameter,
                                          port_thickness=port_thickness,
                                          mount_inst=top_hub,
                                          mount_conn="LEFT_CONNECTOR")

    motor_model = "MAGiDRIVE150"
    propeller_model = "62x5_2_3200_46_1150"

    top_right_front_motor = designer.add_motor(motor_model,
                                               "top_right_front_motor",
                                               mount_inst=top_right_bar,
                                               mount_conn="RIGHT_CONNECTOR",
                                               controller_inst=battery_controller)

    designer.add_propeller(propeller_model,
                           "top_right_front_prop",
                           prop_type=1,
                           direction=1,
                           motor_inst=top_right_front_motor)

    top_left_bar = designer.add_cylinder("top_left_bar",
                                         length=1600,
                                         diameter=cylinder_diameter,
                                         port_thickness=port_thickness,
                                         mount_inst=top_hub,
                                         mount_conn="RIGHT_CONNECTOR")

    top_left_front_motor = designer.add_motor(motor_model,
                                              "top_left_front_motor",
                                              mount_inst=top_left_bar,
                                              mount_conn="LEFT_CONNECTOR",
                                              controller_inst=battery_controller)

    designer.add_propeller(propeller_model,
                           "top_left_front_prop",
                           prop_type=-1,
                           direction=-1,
                           motor_inst=top_left_front_motor)

    bottom_spacer = designer.add_cylinder("bottom_spacer",
                                          length=spacer_length,
                                          diameter=cylinder_diameter,
                                          port_thickness=port_thickness,
                                          mount_inst=fuselage,
                                          mount_conn="BOTTOM_CONNECTOR")

    bottom_hub = designer.add_cylinder("bottom_hub",
                                       length=cylinder_diameter,
                                       diameter=cylinder_diameter,
                                       port_thickness=port_thickness,
                                       mount_inst=bottom_spacer,
                                       mount_conn="REAR_CONNECTOR")

    bottom_right_bar = designer.add_cylinder("bottom_right_bar",
                                             length=1600,
                                             diameter=cylinder_diameter,
                                             port_thickness=port_thickness,
                                             mount_inst=bottom_hub,
                                             mount_conn="RIGHT_CONNECTOR")

    bottom_right_front_motor = designer.add_motor(motor_model,
                                                  "bottom_right_front_motor",
                                                  mount_inst=bottom_right_bar,
                                                  mount_conn="LEFT_CONNECTOR",
                                                  controller_inst=battery_controller)

    designer.add_propeller(propeller_model,
                           "bottom_right_front_prop",
                           prop_type=-1,
                           direction=-1,
                           motor_inst=bottom_right_front_motor)

    bottom_left_bar = designer.add_cylinder("bottom_left_bar",
                                            length=1600,
                                            diameter=cylinder_diameter,
                                            port_thickness=port_thickness,
                                            mount_inst=bottom_hub,
                                            mount_conn="LEFT_CONNECTOR")

    bottom_left_front_motor = designer.add_motor(motor_model,
                                                 "bottom_left_front_motor",
                                                 mount_inst=bottom_left_bar,
                                                 mount_conn="RIGHT_CONNECTOR",
                                                 controller_inst=battery_controller)

    designer.add_propeller(propeller_model,
                           "bottom_left_front_prop",
                           prop_type=1,
                           direction=1,
                           motor_inst=bottom_left_front_motor)

    # Requested_Lateral_Speed_1=47
    # Requested_Lateral_Speed_3=32
    # Requested_Lateral_Speed_5=22

    designer.close_design()


def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--many-cylinders', action='store_true',
                        help="creates lots of ported cylinders")
    parser.add_argument('--minimal', action='store_true',
                        help="creates a minimal design")
    parser.add_argument('--tail-sitter', action='store_true',
                        help="creates a tail-sitter design")
    args = parser.parse_args(args)

    if args.many_cylinders:
        create_many_cylinders()
    elif args.minimal:
        create_minimal()
    elif args.tail_sitter:
        create_tail_sitter()


if __name__ == '__main__':
    run()
