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
#
#===============================================================================
# UAM Design
# Key Design Feature: Front/Back propeller sets with single set of wings at fuselage

from ..designer import Designer, StudyParam
import random

# Create a single propeller set


def create_vudoo():
    return vudoo_platform("")

# Each run will create a new configuration based on the vudoo design.
# Number of propeller sets (motor/propeller is a set) and if a stear wing exists
# are randomized. When each of the propeller sets are created, a random selection
# of its configuration is choosen, options are "Front", "Rear", "All", "None".


def create_vari_vudoo():
    max_num_prop_sets = 12
    random_num_prop_sets = round(random.uniform(0, max_num_prop_sets))
    has_stear_wing = bool(random.getrandbits(1))
    print("Number of Propeller/Motor sets: %d" % random_num_prop_sets)
    print("Stear Wing exists: %s" % str(has_stear_wing))
    variant_name = "Vari" + str(random_num_prop_sets) + "Sets"
    return vudoo_platform(variant=variant_name, num_prop_sets=random_num_prop_sets, stear_wing=has_stear_wing, random_prop_set_config=True)


def vudoo_platform(variant, num_prop_sets=1, stear_wing=False, random_prop_set_config=False):
    corpus_type = "UAM"
    description = "Study Parameters for Vudoo Platform direct2cad Run"

    design_name = "VUdoo" + variant

    designer = Designer()
    designer.create_design(design_name)

    ########################################
    # Static params
    wing_naca = "0015"
    stear_wing_naca = "0006"
    battery_model = "Tattu25AhLi"
    motor_model = "magicall_MAGiDRIVE300"
    propeller_model = "swri_90x8_2_2000_41_2000"
    prop_set_config = ["Front", "Rear", "All", "None"]

    ########################################
    # Tunable params
    fuse_length = designer.set_study_param("fuse_length", 2000)
    fuse_diameter = designer.set_study_param("fuse_sphere_diameter", 1520)
    fuse_mid_length = designer.set_study_param("fuse_middle_length", 750)
    fuse_tail_diameter = designer.set_study_param("fuse_tail_diameter", 200)
    fuse_floor_height = designer.set_study_param("fuse_floor_height", 150)
    seat1_fb_pos = designer.set_study_param("seat1_fb_pos", 1000)
    seat1_lr_pos = designer.set_study_param("seat1_lr_pos", -210)
    seat2_fb_pos = designer.set_study_param("seat2_fb_pos", 1000)
    seat2_lr_pos = designer.set_study_param("seat2_lr_pos", 210)
    fuse_top_disp = designer.set_study_param("fuse_top_disp", 300)
    fuse_bottom_disp = designer.set_study_param("fuse_bottom_disp", 300)
    fuse_left_disp = designer.set_study_param("fuse_left_disp", 0)
    fuse_rigth_disp = designer.set_study_param("fuse_right_disp", 0)

    wing_chord = designer.set_study_param("wing_chord", 1200)
    wing_span = designer.set_study_param("wing_span", 10000)
    wing_load = designer.set_study_param("wing_load", 15000)

    battery_voltage = designer.set_study_param(
        "battery_voltage", 569)  # rounded up
    percent = 88 * 7000 / 10000    # rounded down
    battery_percent = designer.set_study_param("battery_percent", percent)

    cylinder_diameter = designer.set_study_param("cylinder_diameter", 100)
    port_thickness = 0.75 * designer.param_value(cylinder_diameter)
    spacer1_length = designer.set_study_param("spacer1_length", 500)
    spacer2_length = designer.set_study_param("spacer2_length", 1300)
    spacer3_length = 2 * \
        designer.param_value(spacer2_length) + \
        designer.param_value(cylinder_diameter)

    valid_cylinder = 8 <= port_thickness < designer.param_value(
        cylinder_diameter) <= designer.param_value(spacer1_length)
    assert valid_cylinder

    stear_wing_chord = designer.set_study_param("stear_wing_chord", 500)
    stear_wing_span = designer.set_study_param("stear_wing_span", 2000)
    stear_wing_load = designer.set_study_param("stear_wing_load", 1000)
    stear_bar1_length = designer.set_study_param("stear_bar1_length", 4000)

    ########################################
    # Center (Fuselage and Passenger Seats)
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

    for count in range(0, num_prop_sets):
        if random_prop_set_config:
            selected_prop_set_config = random.choice(prop_set_config)
        else:
            # All four propellers
            selected_prop_set_config = "All"
        print("Propeller/Motor Configuration: %s" %
              selected_prop_set_config)
        if selected_prop_set_config != "None":
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
            # Add motor/propellers for "Front" and "All" configurations
            if selected_prop_set_config != "Rear":
                designer.add_motor_propeller(motor_model=motor_model,
                                             prop_model=propeller_model,
                                             prop_type=1,
                                             direction=1,
                                             name_prefix="top_right_front{}".format(
                                                 count),
                                             mount_inst=top_right_hub,
                                             mount_conn="RIGHT_CONNECTOR",
                                             controller_inst=battery_controller)
            # Add motor/propellers for "Rear" and "All" configuration
            if selected_prop_set_config != "Front":
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
            # Add motor_propellers for "Front" and "All" configuration
            if selected_prop_set_config != "Rear":
                designer.add_motor_propeller(motor_model=motor_model,
                                             prop_model=propeller_model,
                                             name_prefix="top_left_front{}".format(
                                                 count),
                                             prop_type=-1,
                                             direction=-1,
                                             mount_inst=top_left_hub,
                                             mount_conn="LEFT_CONNECTOR",
                                             controller_inst=battery_controller)
            # Add motor/propellers for "Rear" and "All" configuration
            if selected_prop_set_config != "Front":
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
            # Add motor_propellers for "Front" and "All" configuration
            if selected_prop_set_config != "Rear":
                designer.add_motor_propeller(motor_model=motor_model,
                                             prop_model=propeller_model,
                                             name_prefix="bottom_right_front{}".format(
                                                 count),
                                             prop_type=-1,
                                             direction=-1,
                                             mount_inst=bottom_right_hub,
                                             mount_conn="LEFT_CONNECTOR",
                                             controller_inst=battery_controller)
            # Add motor/propellers for "Rear" and "All" configuration
            if selected_prop_set_config != "Front":
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
            # Add motor_propellers for "Front" and "All" configuration
            if selected_prop_set_config != "Rear":
                designer.add_motor_propeller(motor_model=motor_model,
                                             prop_model=propeller_model,
                                             name_prefix="bottom_left_front{}".format(
                                                 count),
                                             prop_type=1,
                                             direction=1,
                                             mount_inst=bottom_left_hub,
                                             mount_conn="RIGHT_CONNECTOR",
                                             controller_inst=battery_controller)
            # Add motor/propellers for "Rear" and "All" configuration
            if selected_prop_set_config != "Front":
                designer.add_motor_propeller(motor_model=motor_model,
                                             prop_model=propeller_model,
                                             name_prefix="bottom_left_rear{}".format(
                                                 count),
                                             prop_type=1,
                                             direction=-1,
                                             mount_inst=bottom_left_hub,
                                             mount_conn="LEFT_CONNECTOR",
                                             controller_inst=battery_controller)

    ########################################
    # Stear Wing
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

    study_params = [
        StudyParam("Analysis_Type", 3, "FDM"),
        StudyParam("Flight_Path", [1, 3, 4, 5], "FDM"),
        StudyParam("Requested_Lateral_Speed_1", 48, "FDM"),
        StudyParam("Requested_Lateral_Speed_5", 31, "FDM"),
        StudyParam("Q_Position_5", 0.01, "FDM"),
        StudyParam("Q_Velocity_5", 0.01, "FDM"),
        StudyParam("Q_Angular_Velocity_5", 0.1, "FDM"),
        StudyParam("Q_Angles_5", 0.01, "FDM"),
        StudyParam("R_5", 0.1, "FDM"),
    ]

    # Add all study parameters automatically
    for val in locals().values():
        if isinstance(val, StudyParam):
            study_params.append(val)

    return design_name, description, corpus_type, study_params
