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


def create_minimal():
    designer = Designer()
    designer.create_design("Minimal")
    designer.add_fuselage(name="fuselage",
                          length=2000,
                          sphere_diameter=1520,
                          middle_length=300,
                          tail_diameter=200,
                          floor_height=150,
                          seat_1_fb=1000,
                          seat_1_lr=-210,
                          seat_2_fb=1000,
                          seat_2_lr=210)
    designer.close_design()


def create_tail_sitter():
    designer = Designer()

    if False:
        designer.create_design("TailSitter3NarrowBody")

        fuselage = designer.add_fuselage(name="fuselage",
                                         length=2345,
                                         sphere_diameter=1201,
                                         middle_length=1517,
                                         tail_diameter=107,
                                         floor_height=110,
                                         seat_1_fb=1523,
                                         seat_1_lr=0,
                                         seat_2_fb=690,
                                         seat_2_lr=0,
                                         top_port_disp=0,
                                         bottom_port_disp=0,
                                         left_port_disp=0,
                                         right_port_disp=0)

        wing_naca = "0015"
        wing_chord = 1400
        wing_span = 8000
        wing_load = 5000

        battery_model = "VitalyBeta"
        battery_voltage = 840
        battery_percent = 100

        cylinder_diameter = 100
        port_thickness = 0.75 * cylinder_diameter
        bar1_length = 1000
        bar2_length = 750

        motor_model = "MAGiDRIVE150"
        propeller_model = "62x5_2_3200_46_1150"

        has_stear_wing = True
        stear_wing_naca = "0006"
        stear_wing_chord = 500
        stear_wing_span = 3000
        stear_wing_load = 1000

    else:
        designer.create_design("TailSitter3JoyRide")

        fuselage = designer.add_fuselage(name="fuselage",
                                         length=500,
                                         sphere_diameter=160,
                                         middle_length=400,
                                         tail_diameter=100,
                                         floor_height=130,
                                         seat_1_fb=1400,
                                         seat_1_lr=0,
                                         seat_2_fb=2300,
                                         seat_2_lr=0,
                                         port_thickness=75,
                                         left_port_disp=-550,
                                         right_port_disp=-550)

        wing_naca = "0015"
        wing_chord = 1400
        wing_span = 8000
        wing_load = 5000

        battery_model = "VitalyBeta"
        battery_voltage = 840
        battery_percent = 100

        cylinder_diameter = 100
        port_thickness = 0.75 * cylinder_diameter
        bar1_length = 700
        bar2_length = 750

        motor_model = "MAGiDRIVE150"
        propeller_model = "62x5_2_3200_46_1150"

        has_stear_wing = True
        stear_wing_naca = "0006"
        stear_wing_chord = 500
        stear_wing_span = 3000
        stear_wing_load = 1000

    designer.add_passenger(name="passenger1",
                           fuselage_inst=fuselage,
                           fuselage_conn="SEAT_1_CONNECTOR")
    designer.add_passenger(name="passenger2",
                           fuselage_inst=fuselage,
                           fuselage_conn="SEAT_2_CONNECTOR")

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

    designer.add_motor_propeller(motor_model=motor_model,
                                 prop_model=propeller_model,
                                 prop_type=1,
                                 direction=1,
                                 name_prefix="top_right_front",
                                 mount_inst=top_right_hub,
                                 mount_conn="RIGHT_CONNECTOR",
                                 controller_inst=battery_controller)

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

    designer.add_motor_propeller(motor_model=motor_model,
                                 prop_model=propeller_model,
                                 prop_type=-1,
                                 direction=-1,
                                 name_prefix="top_left_front",
                                 mount_inst=top_left_hub,
                                 mount_conn="LEFT_CONNECTOR",
                                 controller_inst=battery_controller)

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

    designer.add_motor_propeller(motor_model=motor_model,
                                 prop_model=propeller_model,
                                 prop_type=-1,
                                 direction=-1,
                                 name_prefix="bottom_right_front",
                                 mount_inst=bottom_right_hub,
                                 mount_conn="LEFT_CONNECTOR",
                                 controller_inst=battery_controller)

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

    designer.add_motor_propeller(motor_model=motor_model,
                                 prop_model=propeller_model,
                                 prop_type=1,
                                 direction=1,
                                 name_prefix="bottom_left_front",
                                 mount_inst=bottom_left_hub,
                                 mount_conn="RIGHT_CONNECTOR",
                                 controller_inst=battery_controller)

    if has_stear_wing:
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
                                           front_angle=45,
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
                          left_conn="TOP_CONNECTOR")

    designer.set_config_param("Requested_Lateral_Speed_1", 50)
    designer.set_config_param("Requested_Lateral_Speed_3", 32)
    designer.set_config_param("Requested_Lateral_Speed_5", 46)
    designer.set_config_param("Q_Position_5", 0.01)
    designer.set_config_param("Q_Velocity_5", 0.1)
    designer.set_config_param("Q_Angles_5", 1.0)
    designer.set_config_param("Q_Angular_Velocity_5", 0.1)
    designer.set_config_param("R_5", 0.1)

    designer.close_design()


def create_vudoo():
    designer = Designer()
    designer.create_design("VUdoo5")

    fuselage = designer.add_fuselage(name="fuselage",
                                     length=2000,
                                     sphere_diameter=1520,
                                     middle_length=750,
                                     tail_diameter=200,
                                     floor_height=150,
                                     seat_1_fb=1000,
                                     seat_1_lr=-210,
                                     seat_2_fb=1000,
                                     seat_2_lr=210,
                                     top_port_disp=300,
                                     bottom_port_disp=300,
                                     left_port_disp=0,
                                     right_port_disp=0)

    wing_naca = "0015"
    wing_chord = 1200
    wing_span = 10000
    wing_load = 15000

    battery_model = "Tattu25AhLi"
    battery_voltage = 569   # rounded up
    battery_percent = 88 * 7000 / 10000    # rounded down

    cylinder_diameter = 100
    port_thickness = 0.75 * cylinder_diameter
    spacer1_length = 500
    spacer2_length = 1300
    spacer3_length = 2 * spacer2_length + cylinder_diameter

    motor_model = "MAGiDRIVE300"
    propeller_model = "90x8_2_2000_41_2000"

    has_stear_wing = False
    stear_wing_naca = "0006"
    stear_wing_chord = 500
    stear_wing_span = 2000
    stear_wing_load = 1000

    designer.set_config_param("Requested_Lateral_Speed_1", 48)
    designer.set_config_param("Requested_Lateral_Speed_5", 31)
    designer.set_config_param("Q_Position_5", 0.01)
    designer.set_config_param("Q_Velocity_5", 0.01)
    designer.set_config_param("Q_Angular_Velocity_5", 0.1)
    designer.set_config_param("Q_Angles_5", 0.01)
    designer.set_config_param("R_5", 0.1)

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

    for count in range(0, 1):
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

    if has_stear_wing:
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
                                           front_angle=45,
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
                          left_conn="TOP_CONNECTOR")

    designer.close_design()


def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('design', choices=[
        "minimal",
        "tail-sitter",
        "vudoo",
    ])
    args = parser.parse_args(args)

    if args.design == "minimal":
        create_minimal()
    elif args.design == "tail-sitter":
        create_tail_sitter()
    elif args.design == "vudoo":
        create_vudoo()
    else:
        raise ValueError("unknown design")


if __name__ == '__main__':
    run()
