#!/usr/bin/env python3
# Copyright (C) 2022, Peter Volgyesi
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

# UAM Design
# Key Design Feature: 4 propellers in front, 2 wings and a stear wing
from ..designer import Designer, StudyParam


def create_tailsitter_narrow():
    return tailsitter_platform("NarrowBody", narrow=True, stear_wing=True)


def create_tailsitter_joyride():
    return tailsitter_platform("JoyRide", stear_wing=True)


def tailsitter_platform(variant, narrow=False, stear_wing=False):
    design_name = "TailSitter3" + variant

    designer = Designer()
    designer.create_design(design_name)

    ########################################
    # Static params
    wing_naca = "0015"
    stear_wing_naca = "0006"
    battery_model = "VitalyBeta"
    motor_model = "magicall_MAGiDRIVE150"
    propeller_model = "swri_62x5_2_3200_46_1150"

    ########################################
    # Tunable params
    if narrow:
        fuse_length = designer.set_study_param("fuse_length", 2345)
        fuse_diameter = designer.set_study_param("fuse_diameter", 1201)
        fuse_mid_length = designer.set_study_param("fuse_mid_length", 1517)
        fuse_tail_diameter = designer.set_study_param(
            "fuse_tail_diameter", 107)
        fuse_floor_height = designer. set_study_param("fuse_floor_height", 110)
        seat1_fb_pos = designer.set_study_param("seat1_fb_pos", 1523)
        seat1_lr_pos = designer.set_study_param("seat1_lr_pos", 0)
        seat2_fb_pos = designer.set_study_param("seat2_fb_pos", 690)
        seat2_lr_pos = designer.set_study_param("seat2_lr_pos", 0)
        fuse_port_thickness = designer.set_study_param(
            "fuse_port_thickness", 100)
        fuse_top_disp = designer.set_study_param("fuse_top_disp", 0)
        fuse_bottom_disp = designer.set_study_param("fuse_bottom_disp", 0)
        fuse_left_disp = designer.set_study_param("fuse_left_disp", 0)
        fuse_rigth_disp = designer.set_study_param("fuse_right_disp", 0)
        bar1_length = designer.set_study_param("bar1_length", 1000)
        bar2_length = designer.set_study_param("bar2_length", 750)
    else:
        fuse_length = designer.set_study_param("fuse_length", 500)
        fuse_diameter = designer.set_study_param("fuse_diameter", 160)
        fuse_mid_length = designer.set_study_param("fuse_mid_length", 400)
        fuse_tail_diameter = designer.set_study_param(
            "fuse_tail_diameter", 100)
        fuse_floor_height = designer. set_study_param("fuse_floor_height", 130)
        seat1_fb_pos = designer.set_study_param("seat1_fb_pos", 1400)
        seat1_lr_pos = designer.set_study_param("seat1_lr_pos", 0)
        seat2_fb_pos = designer.set_study_param("seat2_fb_pos", 2300)
        seat2_lr_pos = designer.set_study_param("seat2_lr_pos", 0)
        fuse_port_thickness = designer.set_study_param(
            "fuse_port_thickness", 75)
        fuse_top_disp = designer.set_study_param("fuse_top_disp", 0)
        fuse_bottom_disp = designer.set_study_param("fuse_bottom_disp", 0)
        fuse_left_disp = designer.set_study_param("fuse_left_disp", -550)
        fuse_rigth_disp = designer.set_study_param("fuse_right_disp", -550)
        bar1_length = designer.set_study_param("bar1_length", 700)
        bar2_length = designer.set_study_param("bar2_length", 750)

    wing_chord = designer.set_study_param("wing_chord", 1400)
    wing_span = designer.set_study_param("wing_span", 8000)
    wing_load = designer.set_study_param("wing_load", 5000)

    battery_voltage = designer.set_study_param("battery_voltage", 840)
    battery_percent = designer.set_study_param("battery_percent", 100)

    cylinder_diameter = designer.set_study_param("cylinder_diameter", 100)
    port_thickness = 0.75 * designer.param_value(cylinder_diameter)

    stear_wing_chord = designer.set_study_param("stear_wing_chord", 500)
    stear_wing_span = designer.set_study_param("stear_wing_span", 3000)
    stear_wing_load = designer.set_study_param("stear_wing_load", 1000)
    stear_bar1_length = designer.set_study_param("stear_bar1_length", 4000)

    ########################################
    # Center (Fuselage and passenger seats)
    fuselage = designer.add_fuselage_uam(name="fuselage",
                                         length=fuse_length,
                                         sphere_diameter=fuse_diameter,
                                         middle_length=fuse_mid_length,
                                         tail_diameter=fuse_tail_diameter,
                                         floor_height=fuse_floor_height,
                                         seat_1_fb=seat1_fb_pos,
                                         seat_1_lr=seat1_lr_pos,
                                         seat_2_fb=seat2_fb_pos,
                                         seat_2_lr=seat2_lr_pos,
                                         port_thickness=fuse_port_thickness,
                                         top_port_disp=fuse_top_disp,
                                         bottom_port_disp=fuse_bottom_disp,
                                         left_port_disp=fuse_left_disp,
                                         right_port_disp=fuse_rigth_disp)
    designer.add_passenger(name="passenger1",
                           fuselage_inst=fuselage,
                           fuselage_conn="SEAT_1_CONNECTOR")
    designer.add_passenger(name="passenger2",
                           fuselage_inst=fuselage,
                           fuselage_conn="SEAT_2_CONNECTOR")

    ########################################
    # Main Wings and Batteries
    right_wing = designer.add_wing_uam(name="right_wing",
                                       naca=wing_naca,
                                       chord=wing_chord,
                                       span=wing_span,
                                       load=wing_load,
                                       left_inst=fuselage,
                                       left_conn="RIGHT_CONNECTOR")
    left_wing = designer.add_wing_uam(name="left_wing",
                                      naca=wing_naca,
                                      chord=wing_chord,
                                      span=wing_span,
                                      load=wing_load,
                                      right_inst=fuselage,
                                      right_conn="LEFT_CONNECTOR")

    battery_controller = designer.add_battery_controller("battery_controller")
    designer.add_battery_uam(battery_model,
                             name="right_battery",
                             naca=wing_naca,
                             chord=wing_chord,
                             span=wing_span,
                             mount_side=1,
                             voltage_request=battery_voltage,
                             volume_percent=battery_percent,
                             wing_inst=right_wing,
                             controller_inst=battery_controller)
    designer.add_battery_uam(battery_model,
                             name="left_battery",
                             naca=wing_naca,
                             chord=wing_chord,
                             span=wing_span,
                             mount_side=2,
                             voltage_request=battery_voltage,
                             volume_percent=battery_percent,
                             wing_inst=left_wing,
                             controller_inst=battery_controller)

    ########################################
    # Main Structure (cylinders/motors/propellers)
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

    ########################################
    # Stear Wings
    if stear_wing:
        stear_bar1 = designer.add_cylinder(name="stear_bar1",
                                           length=stear_bar1_length,
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
        designer.add_wing_uam(name="right_stear_wing",
                              naca=stear_wing_naca,
                              chord=stear_wing_chord,
                              span=stear_wing_span,
                              load=stear_wing_load,
                              left_inst=stear_bar2,
                              left_conn="RIGHT_CONNECTOR")
        designer.add_wing_uam(name="left_stear_wing",
                              naca=stear_wing_naca,
                              chord=stear_wing_chord,
                              span=stear_wing_span,
                              load=stear_wing_load,
                              left_inst=stear_bar2,
                              left_conn="TOP_CONNECTOR")

    designer.close_design(corpus="uam")

    # MM TODO: set FDM Parameter for UAM (list of settings - commented below)
    study_params = {
        "Analysis_Type": 3,
        "Flight_Path": 1,
        "Requested_Lateral_Speed": 50,
        "Requested_Vertical_Speed": 19,
        "Q_Position": 1,
        "Q_Velocity": 1,
        "Q_Angular_Velocity": 1,
        "Q_Angles": 1,
        "Ctrl_R": 1,
    }

    """    design_fdm_parameters = {
        "Analysis_Type": 3,
        "Flight_Path": [1, 3, 4, 5],
        "Requested_Lateral_Speed": [50, 32, 1, 46],
        "Requested_Vertical_Speed": 19,
        "Q_Position": [1, 1, 1, 0.01],
        "Q_Velocity": [1, 1, 1, 0.1],
        "Q_Angular_Velocity": [1, 1, 1, 0.1],
        "Q_Angles": 1,
        "Ctrl_R": 0.1
    }
    """

    # Add all study parameters automatically
    for val in locals().values():
        if isinstance(val, StudyParam):
            study_params[val.name] = val.value

    return design_name, study_params
