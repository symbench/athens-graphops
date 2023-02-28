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
# UAV Design
# Key Design Feature: Minimal design elements

from ..designer import Designer, StudyParam

# Cargo case attached but empty


def create_minimal_uav():
    return minimal_platform("", with_cargo=False, single_battery=True)


def create_minimal_uav_cargo():
    return minimal_platform("Cargo", with_cargo=True, single_battery=False)


def minimal_platform(variant, with_cargo=False, single_battery=False):
    corpus_type = "UAV"
    description = "Study Parameters for Minimal Platform direct2cad Run"
    design_name = "MinimalUAV" + variant

    designer = Designer()
    designer.create_design(design_name)

    ########################################
    # Static params
    main_hub_connects = 3
    battery_type = "TurnigyGraphene6000mAh6S75C"

    if single_battery:
        battery1_placement = 0
    else:
        battery1_placement = 30

    ########################################
    # Tunable params
    if with_cargo:
        cargo_mass = designer.set_study_param("CargoMass", [0.5], "CargoMass")
    else:
        cargo_mass = designer.set_study_param("CargoMass", [0.001], "CargoMass")

    fuselage_floor_height = designer.set_study_param(
        "fuselage_floor_height", 20)
    fuselage_width = designer.set_study_param("fuselage_width", 190)
    fuselage_height = designer.set_study_param("fuselage_height", 125)
    fuselage_cyl_length = designer.set_study_param("fuselage_cyl_length", 270)
    bott_conn_rotation = designer.set_study_param("bott_conn_rotation", 45)
    hub_conn_hort_angle = designer.set_study_param("hub_conn_hort_angle", 90)
    z_angle = designer.set_study_param("z_angle", 45)

    ########################################
    # Center (Hub, Fuselage, Cargo)
    fuselage = designer.add_fuselage_uav(name="fuselage",
                                         floor_height=fuselage_floor_height,
                                         fuse_width=fuselage_width,
                                         fuse_height=fuselage_height,
                                         fuse_cyl_length=fuselage_cyl_length,
                                         bottom_connector_rotation=bott_conn_rotation)
    cargo_mass_list = designer.param_value(cargo_mass)
    cargo, cargo_case = designer.add_cargo(weight=cargo_mass_list[0],
                                           name="cargo")

    # Require main_hub for connection to Orient
    # Create hub connection lists (size of num_connections max)
    # Not all connections are needed
    designer.add_hub(name="main_hub",
                     num_connects=main_hub_connects,
                     connector_horizonal_angle=hub_conn_hort_angle,
                     connects=["Top_Connector", "Bottom_Connector"],
                     mount_inst=[fuselage, cargo_case],
                     mount_conn=["BottomConnector", "Case2HubConnector"],
                     orient_base=True)

    ########################################
    # Batteries
    battery_control = designer.add_battery_controller(name="BatteryController")
    designer.add_battery_uav(model=battery_type,
                             name="Battery_1",
                             fuse_conn_num=1,
                             mount_length=0,
                             mount_width=battery1_placement,
                             controller_inst=battery_control)

    if not single_battery:
        designer.add_battery_uav(model=battery_type,
                                 name="Battery_2",
                                 fuse_conn_num=2,
                                 mount_length=0,
                                 mount_width=-battery1_placement,
                                 controller_inst=battery_control)

    ########################################
    # Sensors
    designer.add_sensor(sensor_model="RpmTemp",
                        name="RpmTemp",
                        mount_conn_num=3,
                        rotation=90,
                        mount_length=-160,
                        mount_width=13)
    designer.add_sensor(sensor_model="Current",
                        name="Current",
                        mount_conn_num=4,
                        rotation=90,
                        mount_length=-160,
                        mount_width=-18)
    designer.add_sensor(sensor_model="Autopilot",
                        name="Autopilot",
                        mount_conn_num=5,
                        rotation=90,
                        mount_length=115,
                        mount_width=0)
    designer.add_sensor(sensor_model="Voltage",
                        name="Voltage",
                        mount_conn_num=6,
                        rotation=90,
                        mount_length=155,
                        mount_width=18)
    designer.add_sensor(sensor_model="GPS",
                        name="GPS",
                        mount_conn_num=7,
                        mount_length=-120,
                        mount_width=0)
    designer.add_sensor(sensor_model="Variometer",
                        name="Variometer",
                        mount_conn_num=8,
                        rotation=90,
                        mount_length=155,
                        mount_width=-18)

    designer.close_design(corpus="uav", orient_z_angle=z_angle)

    study_params = [
        StudyParam("Flight_Path", 9, "FDM"),
        StudyParam("Requested_Lateral_Speed", 23, "FDM"),
        StudyParam("Requested_Vertical_Speed", -5, "FDM"),
        StudyParam("Requested_Vertical_Down_Speed", 5, "FDM"),
        StudyParam("Requested_Lateral_Acceleration", 2, "FDM"),
        StudyParam("Requested_Lateral_Deceleration", -3, "FDM"),
        StudyParam("Requested_Vertical_Acceleration", -1, "FDM"),
        StudyParam("Requested_Vertical_Deceleration", 1, "FDM"),
        # James suggested not to tweak these
        # StudyParam("Landing_Approach_Height", 3, "FDM"),
        # StudyParam("Vertical_Landing_Speed", 0.5, "FDM"),    # not used in buildcad.py
        # StudyParam("Vertical_Landing_Speed_At_Ground", 0.1, "FDM"),
        StudyParam("Q_Position", 1, "FDM"),
        StudyParam("Q_Velocity", 0.5, "FDM"),
        StudyParam("Q_Angular_Velocity", 1, "FDM"),
        StudyParam("Q_Angles", 0.5, "FDM"),
        StudyParam("Ctrl_R", 0.25, "FDM"),
    ]

    # Add all study parameters automatically
    for val in locals().values():
        if isinstance(val, StudyParam):
            study_params.append(val)

    return design_name, description, corpus_type, study_params
