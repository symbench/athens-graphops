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

        self.fuselage = self.add_instance("FUSE_SPHERE_CYL_CONE", "fuselage")
        self.orient = self.add_instance("Orient", "Orient")
        self.connect(self.orient, "ORIENTCONN", self.fuselage, "ORIENT")
        return self.fuselage

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
                    name=designer.get_name(),
                    port_thickness=port_thickness,
                    diameter=diameter,
                    length=length)
                designer.connect(previous, "REAR_CONNECTOR",
                                 instance, "FRONT_CONNECTOR")
                previous = instance

    designer.close_design()


def create_tail_sitter():
    designer = Designer()
    fuselage = designer.create_design("TailSitter3")

    designer.add_passenger(name="passenger1",
                           fuselage_inst=fuselage,
                           fuselage_conn="SEAT_1_CONNECTOR")
    designer.add_passenger(name="passenger2",
                           fuselage_inst=fuselage,
                           fuselage_conn="SEAT_2_CONNECTOR")

    wing_naca = "2418"
    wing_chord = 1000
    wing_span = 10000
    wing_load = 10000

    right_wing = designer.add_wing(name="right_wing",
                                   naca=wing_naca,
                                   chord=wing_chord,
                                   span=wing_span,
                                   load=wing_load,
                                   left_inst=fuselage,
                                   left_conn="RIGHT_CONNECTOR")

    left_wing = designer.add_wing(name="left_wing",
                                  naca=wing_naca,
                                  chord=wing_chord,
                                  span=wing_span,
                                  load=wing_load,
                                  right_inst=fuselage,
                                  right_conn="LEFT_CONNECTOR")

    battery_controller = designer.add_battery_controller("battery_controller")
    battery_model = "VitalyBeta"
    battery_voltage = 840
    battery_percent = 100

    designer.add_battery(battery_model,
                         name="right_battery",
                         naca=wing_naca,
                         chord=wing_chord,
                         span=wing_span,
                         mount_side=1,
                         voltage_request=battery_voltage,
                         volume_percent=battery_percent,
                         wing_inst=right_wing,
                         controller_inst=battery_controller)

    designer.add_battery(battery_model,
                         name="left_battery",
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
    bar1_length = 600
    bar2_length = 750

    top_bar = designer.add_cylinder(name="top_bar",
                                    length=bar1_length,
                                    diameter=cylinder_diameter,
                                    port_thickness=port_thickness,
                                    mount_inst=fuselage,
                                    mount_conn="TOP_CONNECTOR")

    top_hub = designer.add_cylinder(name="top_hub",
                                    length=cylinder_diameter,
                                    diameter=cylinder_diameter,
                                    port_thickness=port_thickness,
                                    mount_inst=top_bar,
                                    mount_conn="REAR_CONNECTOR")

    top_right_bar = designer.add_cylinder(name="top_right_bar",
                                          length=bar2_length,
                                          diameter=cylinder_diameter,
                                          port_thickness=port_thickness,
                                          mount_inst=top_hub,
                                          mount_conn="LEFT_CONNECTOR")

    top_right_hub = designer.add_cylinder(name="top_right_hub",
                                          length=cylinder_diameter,
                                          diameter=cylinder_diameter,
                                          port_thickness=port_thickness,
                                          mount_inst=top_right_bar,
                                          mount_conn="REAR_CONNECTOR")

    motor_model = "MAGiDRIVE150"
    propeller_model = "62x5_2_3200_46_1150"

    top_right_front_motor = designer.add_motor(motor_model,
                                               name="top_right_front_motor",
                                               mount_inst=top_right_hub,
                                               mount_conn="RIGHT_CONNECTOR",
                                               controller_inst=battery_controller)

    designer.add_propeller(propeller_model,
                           name="top_right_front_prop",
                           prop_type=1,
                           direction=1,
                           motor_inst=top_right_front_motor)

    top_left_bar = designer.add_cylinder(name="top_left_bar",
                                         length=bar2_length,
                                         diameter=cylinder_diameter,
                                         port_thickness=port_thickness,
                                         mount_inst=top_hub,
                                         mount_conn="RIGHT_CONNECTOR")

    top_left_hub = designer.add_cylinder(name="top_left_hub",
                                         length=cylinder_diameter,
                                         diameter=cylinder_diameter,
                                         port_thickness=port_thickness,
                                         mount_inst=top_left_bar,
                                         mount_conn="REAR_CONNECTOR")

    top_left_front_motor = designer.add_motor(motor_model,
                                              name="top_left_front_motor",
                                              mount_inst=top_left_hub,
                                              mount_conn="LEFT_CONNECTOR",
                                              controller_inst=battery_controller)

    designer.add_propeller(propeller_model,
                           name="top_left_front_prop",
                           prop_type=-1,
                           direction=-1,
                           motor_inst=top_left_front_motor)

    bottom_bar = designer.add_cylinder(name="bottom_bar",
                                       length=bar1_length,
                                       diameter=cylinder_diameter,
                                       port_thickness=port_thickness,
                                       mount_inst=fuselage,
                                       mount_conn="BOTTOM_CONNECTOR")

    bottom_hub = designer.add_cylinder(name="bottom_hub",
                                       length=cylinder_diameter,
                                       diameter=cylinder_diameter,
                                       port_thickness=port_thickness,
                                       mount_inst=bottom_bar,
                                       mount_conn="REAR_CONNECTOR")

    bottom_right_bar = designer.add_cylinder(name="bottom_right_bar",
                                             length=bar2_length,
                                             diameter=cylinder_diameter,
                                             port_thickness=port_thickness,
                                             mount_inst=bottom_hub,
                                             mount_conn="RIGHT_CONNECTOR")

    bottom_right_hub = designer.add_cylinder(name="bottom_right_hub",
                                             length=cylinder_diameter,
                                             diameter=cylinder_diameter,
                                             port_thickness=port_thickness,
                                             mount_inst=bottom_right_bar,
                                             mount_conn="REAR_CONNECTOR")

    bottom_right_front_motor = designer.add_motor(motor_model,
                                                  name="bottom_right_front_motor",
                                                  mount_inst=bottom_right_hub,
                                                  mount_conn="LEFT_CONNECTOR",
                                                  controller_inst=battery_controller)

    designer.add_propeller(propeller_model,
                           name="bottom_right_front_prop",
                           prop_type=-1,
                           direction=-1,
                           motor_inst=bottom_right_front_motor)

    bottom_left_bar = designer.add_cylinder(name="bottom_left_bar",
                                            length=bar2_length,
                                            diameter=cylinder_diameter,
                                            port_thickness=port_thickness,
                                            mount_inst=bottom_hub,
                                            mount_conn="LEFT_CONNECTOR")

    bottom_left_hub = designer.add_cylinder(name="bottom_left_hub",
                                            length=cylinder_diameter,
                                            diameter=cylinder_diameter,
                                            port_thickness=port_thickness,
                                            mount_inst=bottom_left_bar,
                                            mount_conn="REAR_CONNECTOR")

    bottom_left_front_motor = designer.add_motor(motor_model,
                                                 name="bottom_left_front_motor",
                                                 mount_inst=bottom_left_hub,
                                                 mount_conn="RIGHT_CONNECTOR",
                                                 controller_inst=battery_controller)

    designer.add_propeller(propeller_model,
                           name="bottom_left_front_prop",
                           prop_type=1,
                           direction=1,
                           motor_inst=bottom_left_front_motor)

    stear_wing_naca = "0006"
    stear_wing_chord = 500
    stear_wing_span = 2000
    stear_wing_load = 1000

    stear_bar1 = designer.add_cylinder(name="stear_bar1",
                                       length=4000,
                                       diameter=cylinder_diameter,
                                       port_thickness=port_thickness,
                                       mount_inst=fuselage,
                                       mount_conn="REAR_CONNECTOR")

    stear_bar2 = designer.add_cylinder(name="stear_bar2",
                                       length=stear_wing_chord,
                                       diameter=cylinder_diameter,
                                       port_thickness=port_thickness,
                                       front_angle=0,
                                       mount_inst=stear_bar1,
                                       mount_conn="REAR_CONNECTOR")

    designer.add_wing(name="right_stear_wing",
                      naca=stear_wing_naca,
                      chord=stear_wing_chord,
                      span=stear_wing_span,
                      load=stear_wing_load,
                      left_inst=stear_bar2,
                      left_conn="RIGHT_CONNECTOR")

    designer.add_wing(name="left_stear_wing",
                      naca=stear_wing_naca,
                      chord=stear_wing_chord,
                      span=stear_wing_span,
                      load=stear_wing_load,
                      left_inst=stear_bar2,
                      left_conn="LEFT_CONNECTOR")

    designer.add_wing(name="top_stear_wing",
                      naca=stear_wing_naca,
                      chord=stear_wing_chord,
                      span=stear_wing_span,
                      load=stear_wing_load,
                      left_inst=stear_bar2,
                      left_conn="TOP_CONNECTOR")

    designer.add_wing(name="bottom_stear_wing",
                      naca=stear_wing_naca,
                      chord=stear_wing_chord,
                      span=stear_wing_span,
                      load=stear_wing_load,
                      left_inst=stear_bar2,
                      left_conn="BOTTOM_CONNECTOR")

    # Requested_Lateral_Speed_1=45 Requested_Lateral_Speed_3=32 Requested_Lateral_Speed_5=36 Q_Position_5=0.01

    designer.close_design()


def create_lattice():
    designer = Designer()
    fuselage = designer.create_design("Lattice1")

    wing_naca = "2418"
    wing_chord = 1000
    wing_span = 5000
    wing_load = 10000

    battery_model = "VitalyBeta"
    battery_voltage = 33
    battery_percent = 50

    cylinder_diameter = 100
    port_thickness = 0.75 * cylinder_diameter
    spacer1_length = 350
    spacer2_length = 350
    spacer3_length = 2 * spacer2_length + cylinder_diameter

    motor_model = "KDE13218XF105"
    propeller_model = "34x3_2_4600_41_250"

    designer.add_passenger(name="passenger1",
                           fuselage_inst=fuselage,
                           fuselage_conn="SEAT_1_CONNECTOR")
    designer.add_passenger(name="passenger2",
                           fuselage_inst=fuselage,
                           fuselage_conn="SEAT_2_CONNECTOR")

    battery_controller = designer.add_battery_controller("battery_controller")

    right_wing = designer.add_wing(name="right_wing",
                                   naca=wing_naca,
                                   chord=wing_chord,
                                   span=wing_span,
                                   load=wing_load,
                                   left_inst=fuselage,
                                   left_conn="RIGHT_CONNECTOR")

    left_wing = designer.add_wing(name="left_wing",
                                  naca=wing_naca,
                                  chord=wing_chord,
                                  span=wing_span,
                                  load=wing_load,
                                  right_inst=fuselage,
                                  right_conn="LEFT_CONNECTOR")

    designer.add_battery(battery_model,
                         name="right_battery",
                         naca=wing_naca,
                         chord=wing_chord,
                         span=wing_span,
                         mount_side=1,
                         voltage_request=battery_voltage,
                         volume_percent=battery_percent,
                         wing_inst=right_wing,
                         controller_inst=battery_controller)

    designer.add_battery(battery_model,
                         name="left_battery",
                         naca=wing_naca,
                         chord=wing_chord,
                         span=wing_span,
                         mount_side=2,
                         voltage_request=battery_voltage,
                         volume_percent=battery_percent,
                         wing_inst=left_wing,
                         controller_inst=battery_controller)

    top_bar = designer.add_cylinder(name="top_bar",
                                    length=spacer1_length,
                                    diameter=cylinder_diameter,
                                    port_thickness=port_thickness,
                                    mount_inst=fuselage,
                                    mount_conn="TOP_CONNECTOR")

    top_hub = designer.add_cylinder(name="top_hub",
                                    length=cylinder_diameter,
                                    diameter=cylinder_diameter,
                                    port_thickness=port_thickness,
                                    mount_inst=top_bar,
                                    mount_conn="REAR_CONNECTOR")

    bottom_bar = designer.add_cylinder(name="bottom_bar",
                                       length=spacer1_length,
                                       diameter=cylinder_diameter,
                                       port_thickness=port_thickness,
                                       mount_inst=fuselage,
                                       mount_conn="BOTTOM_CONNECTOR")

    bottom_hub = designer.add_cylinder(name="bottom_hub",
                                       length=cylinder_diameter,
                                       diameter=cylinder_diameter,
                                       port_thickness=port_thickness,
                                       mount_inst=bottom_bar,
                                       mount_conn="REAR_CONNECTOR")

    top_right_hub = None
    top_left_hub = None
    bottom_right_hub = None
    bottom_left_hub = None

    for count in range(0, 6):
        top_right_bar = designer.add_cylinder(name="top_right_bar{}".format(count),
                                              length=spacer2_length if count == 0 else spacer3_length,
                                              diameter=cylinder_diameter,
                                              port_thickness=port_thickness,
                                              mount_inst=top_hub if count == 0 else top_right_hub,
                                              mount_conn="LEFT_CONNECTOR" if count == 0 else "REAR_CONNECTOR")

        top_right_hub = designer.add_cylinder(name="top_right_hub{}".format(count),
                                              length=cylinder_diameter,
                                              diameter=cylinder_diameter,
                                              port_thickness=port_thickness,
                                              mount_inst=top_right_bar,
                                              mount_conn="REAR_CONNECTOR")

        designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     prop_type=1,
                                     direction=1,
                                     name_prefix="top_right_front{}".format(
                                         count),
                                     mount_inst=top_right_hub,
                                     mount_conn="RIGHT_CONNECTOR",
                                     controller_inst=battery_controller)

        designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     prop_type=1,
                                     direction=-1,
                                     name_prefix="top_right_rear{}".format(
                                         count),
                                     mount_inst=top_right_hub,
                                     mount_conn="LEFT_CONNECTOR",
                                     controller_inst=battery_controller)

        top_left_bar = designer.add_cylinder(name="top_left_bar{}".format(count),
                                             length=spacer2_length if count == 0 else spacer3_length,
                                             diameter=cylinder_diameter,
                                             port_thickness=port_thickness,
                                             mount_inst=top_hub if count == 0 else top_left_hub,
                                             mount_conn="RIGHT_CONNECTOR" if count == 0 else "REAR_CONNECTOR")

        top_left_hub = designer.add_cylinder(name="top_left_hub{}".format(count),
                                             length=cylinder_diameter,
                                             diameter=cylinder_diameter,
                                             port_thickness=port_thickness,
                                             mount_inst=top_left_bar,
                                             mount_conn="REAR_CONNECTOR")

        designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     name_prefix="top_left_front{}".format(
                                         count),
                                     prop_type=-1,
                                     direction=-1,
                                     mount_inst=top_left_hub,
                                     mount_conn="LEFT_CONNECTOR",
                                     controller_inst=battery_controller)

        designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     name_prefix="top_left_rear{}".format(
                                         count),
                                     prop_type=-1,
                                     direction=1,
                                     mount_inst=top_left_hub,
                                     mount_conn="RIGHT_CONNECTOR",
                                     controller_inst=battery_controller)

        bottom_right_bar = designer.add_cylinder(name="bottom_right_bar{}".format(count),
                                                 length=spacer2_length if count == 0 else spacer3_length,
                                                 diameter=cylinder_diameter,
                                                 port_thickness=port_thickness,
                                                 mount_inst=bottom_hub if count == 0 else bottom_right_hub,
                                                 mount_conn="RIGHT_CONNECTOR" if count == 0 else "REAR_CONNECTOR")

        bottom_right_hub = designer.add_cylinder(name="bottom_right_hub{}".format(count),
                                                 length=cylinder_diameter,
                                                 diameter=cylinder_diameter,
                                                 port_thickness=port_thickness,
                                                 mount_inst=bottom_right_bar,
                                                 mount_conn="REAR_CONNECTOR")

        designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     name_prefix="bottom_right_front{}".format(
                                         count),
                                     prop_type=-1,
                                     direction=-1,
                                     mount_inst=bottom_right_hub,
                                     mount_conn="LEFT_CONNECTOR",
                                     controller_inst=battery_controller)

        designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     name_prefix="bottom_right_rear{}".format(
                                         count),
                                     prop_type=-1,
                                     direction=1,
                                     mount_inst=bottom_right_hub,
                                     mount_conn="RIGHT_CONNECTOR",
                                     controller_inst=battery_controller)

        bottom_left_bar = designer.add_cylinder(name="bottom_left_bar{}".format(count),
                                                length=spacer2_length if count == 0 else spacer3_length,
                                                diameter=cylinder_diameter,
                                                port_thickness=port_thickness,
                                                mount_inst=bottom_hub if count == 0 else bottom_left_hub,
                                                mount_conn="LEFT_CONNECTOR" if count == 0 else "REAR_CONNECTOR")

        bottom_left_hub = designer.add_cylinder(name="bottom_left_hub{}".format(count),
                                                length=cylinder_diameter,
                                                diameter=cylinder_diameter,
                                                port_thickness=port_thickness,
                                                mount_inst=bottom_left_bar,
                                                mount_conn="REAR_CONNECTOR")

        designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     name_prefix="bottom_left_front{}".format(
                                         count),
                                     prop_type=1,
                                     direction=1,
                                     mount_inst=bottom_left_hub,
                                     mount_conn="RIGHT_CONNECTOR",
                                     controller_inst=battery_controller)

        designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     name_prefix="bottom_left_rear{}".format(
                                         count),
                                     prop_type=1,
                                     direction=-1,
                                     mount_inst=bottom_left_hub,
                                     mount_conn="LEFT_CONNECTOR",
                                     controller_inst=battery_controller)

    # Requested_Lateral_Speed_1=28 Requested_Lateral_Speed_3=28 Requested_Lateral_Speed_5=28

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
    parser.add_argument('--lattice', action='store_true',
                        help="creates a lattice design")
    args = parser.parse_args(args)

    if args.many_cylinders:
        create_many_cylinders()
    elif args.minimal:
        create_minimal()
    elif args.tail_sitter:
        create_tail_sitter()
    elif args.lattice:
        create_lattice()


if __name__ == '__main__':
    run()