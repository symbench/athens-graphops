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

# UAV Design
from ..designer import Designer, StudyParam

def create_inline():
    return inline_platform("UAV")

def create_uno_inline():
    return inline_platform("Uno")

def create_uno_inline_tail():
    return inline_platform("UnoTail", with_tail=True)


def inline_platform(variant, with_tail=False):
    """
    MM TODO: update 
    """
    design_name = "Inline" + variant

    designer = Designer()
    designer.create_design(design_name)

    ########################################
    # Static params
    tube_od = 7.1374
    NACA_profile = "0012"
    motor_type = "t_motor_AntigravityMN4006KV380"
    prop_type = "apc_propellers_12x3_8SF"

    ########################################
    # Tunable params
    # Tube between main hub and center structure to move fuselage vertically
    fuse_vert_length = designer.set_study_param("fuse_vert_length", 20)

    # Cargo placement
    cargo_tube_length = designer.set_study_param("cargo_tube_length", 305)

    wing_span = designer.set_study_param("wing_span", 550)
    wing_chord = designer.set_study_param("wing_chord", 150)
    wing_thickness = designer.set_study_param("wing_thickness", 12)
    wing_load = designer.set_study_param("wing_load", 30)
    # height placement of wings
    wing_vert_tube_length = designer.set_study_param("wing_vert_tube_length", 50)

    prop_forward_length = designer.set_study_param("prop_forward_length", 250)
    prop_hort_spread_length = designer.set_study_param("prop_hort_spread_length", 160)
    prop_vert_spread_length = designer.set_study_param("prop_vert_spread_length", 210)

    # MM TODO: set CargoMass to 0.001, 0.5
    # Required to run Path 9 which runs with and without cargo
    cargo_mass = designer.set_study_param("CargoMass", 0.5)

    ########################################
    # Calculated params
    # set wing tube offset to the middle of the wing
    tube_offset = designer.set_study_param("tube_offset", designer.param_value(wing_span) / 2)
    # spread horizontal tube out base on wing span
    wing_hort_tube_length = designer.set_study_param("wing_hort_tube_length", designer.param_value(wing_span) - designer.param_value(tube_offset) - 14.93 - (designer.param_value(tube_od) * 1.5) / 2)

    ########################################
    # Center (Hub, Fuselage, Cargo)
    fuselage = designer.add_fuselage_uav(name="fuselage",
                                         floor_height=20,
                                         fuse_width=190,
                                         fuse_height=125,
                                         fuse_cyl_length=270,
                                         bottom_connector_rotation=0)
    cargo, cargo_case = designer.add_cargo(weight=0.5,
                                           name="cargo")

    # Require main_hub for connection to Orient
    # Create hub connection lists (size of num_connections max)
    # Not all connections are needed
    hub_main = designer.add_hub(name="main_hub",
                                num_connects=2,
                                diameter=tube_od,
                                connector_horizonal_angle=0,
                                connector_vertical_angle=180,
                                connects=["Bottom_Connector"],
                                mount_inst=[fuselage],
                                mount_conn=["BottomConnector"])

    ########################################
    # Batteries
    battery_control = designer.add_battery_controller(name="BatteryController")
    designer.add_battery_uav(model="TurnigyGraphene6000mAh6S75C",
                             name="Battery_1",
                             fuse_conn_num=1,
                             mount_length=0,
                             mount_width=30,
                             controller_inst=battery_control)

    designer.add_battery_uav(model="TurnigyGraphene6000mAh6S75C",
                             name="Battery_2",
                             fuse_conn_num=2,
                             mount_length=0,
                             mount_width=-30,
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

    ########################################
    # Tube between main hub and center  
    # structure to move fuselage vertically
    fuse_hub_tube = designer.add_tube(od=tube_od,
                                      length=fuse_vert_length,
                                      end_rotation=180,
                                      name="fuse_hub_tube",
                                      mount_base_inst=hub_main,
                                      mount_base_conn="Top_Connector")
    center_hub = designer.add_hub(name="center_hub",
                                  num_connects=4,
                                  diameter=tube_od,
                                  connector_horizonal_angle=90,
                                  connects=["Bottom_Connector"],
                                  mount_inst=[fuse_hub_tube],
                                  mount_conn=["EndConnection"],
                                  orient_base=True)

    ########################################
    # Cargo Section
    #   tube from 4 way hub (1) to 2 way hub
    center_cargo_tube = designer.add_tube(od=tube_od,
                                          length=cargo_tube_length,
                                          end_rotation=180,
                                          name="center_cargo_tube",
                                          mount_base_inst=center_hub,
                                          mount_base_conn="Side_Connector_1")
    cargo_hub = designer.add_hub(name="cargo_hub",
                                 num_connects=4,
                                 diameter=tube_od,
                                 connector_horizonal_angle=0,
                                 connects=["Side_Connector_2",
                                           "Top_Connector"],
                                 mount_inst=[center_cargo_tube, cargo_case],
                                 mount_conn=["EndConnection", "Case2HubConnector"])

    ########################################
    # Wings
    # - 2 horizontal tubes from 4 way hub (2 & 4) to 2 way hubs
    # - 2 vertical tubes to attach to vertical wings
    wing_hort_tube_l = designer.add_tube(od=tube_od,
                                         length=wing_hort_tube_length,
                                         end_rotation=180,
                                         name="wing_hort_tube_l",
                                         mount_base_inst=center_hub,
                                         mount_base_conn="Side_Connector_2")
    wing_hort_tube_r = designer.add_tube(od=tube_od,
                                         length=wing_hort_tube_length,
                                         end_rotation=180,
                                         name="wing_hort_tube_r",
                                         mount_base_inst=center_hub,
                                         mount_base_conn="Side_Connector_4")
    wing_hub_l = designer.add_hub(name="wing_hub_l",
                                  num_connects=2,
                                  diameter=tube_od,
                                  connector_horizonal_angle=0,
                                  connector_vertical_angle=180,
                                  connects=["Side_Connector_2"],
                                  mount_inst=[wing_hort_tube_l],
                                  mount_conn=["EndConnection"])
    wing_hub_r = designer.add_hub(name="wing_hub_r",
                                  num_connects=2,
                                  diameter=tube_od,
                                  connector_horizonal_angle=0,
                                  connector_vertical_angle=180,
                                  connects=["Side_Connector_1"],
                                  mount_inst=[wing_hort_tube_r],
                                  mount_conn=["EndConnection"])
    wing_vert_tube_l = designer.add_tube(od=tube_od,
                                         length=wing_vert_tube_length,
                                         end_rotation=180,
                                         name="wing_vert_tube_l",
                                         mount_base_inst=wing_hub_l,
                                         mount_base_conn="Top_Connector")
    wing_vert_tube_r = designer.add_tube(od=tube_od,
                                         length=wing_vert_tube_length,
                                         end_rotation=180,
                                         name="wing_vert_tube_r",
                                         mount_base_inst=wing_hub_r,
                                         mount_base_conn="Top_Connector")
    designer.add_wing_uav(direction="Vertical",
                          chord=wing_chord,
                          span=wing_span,
                          thickness=wing_thickness,
                          load=wing_load,
                          naca=NACA_profile,
                          tube_diameter=tube_od,
                          tube_offset=tube_offset,
                          tube_rotation=90,
                          channel=1,
                          name="left_wing",
                          tube_inst=wing_vert_tube_l,
                          tube_conn="EndConnection")
    designer.add_wing_uav(direction="Vertical",
                          chord=wing_chord,
                          span=wing_span,
                          thickness=wing_thickness,
                          load=wing_load,
                          naca=NACA_profile,
                          tube_diameter=tube_od,
                          tube_offset=tube_offset,
                          tube_rotation=270,
                          channel=2,
                          name="right_wing",
                          tube_inst=wing_vert_tube_r,
                          tube_conn="EndConnection")

    ########################################
    # Props / Motors
    # - tube from 4 way hub (3) to 3 way hub
    # - 2 tubes horizontally to 3 way hubs
    # - 2 vertical tubes out from 3 hubs (on each side) to flanges
    # - 4 prop/motors attached to flanges
    center_tube_prop = designer.add_tube(od=tube_od,
                                         length=prop_forward_length,
                                         end_rotation=180,
                                         name="center_tube_prop",
                                         mount_base_inst=center_hub,
                                         mount_base_conn="Side_Connector_3")
    front_hub = designer.add_hub(name="front_hub",
                                 num_connects=3,
                                 diameter=tube_od,
                                 connector_horizonal_angle=90,
                                 connects=["Side_Connector_2"],
                                 mount_inst=[center_tube_prop],
                                 mount_conn=["EndConnection"])
    prop_hort_tube_l = designer.add_tube(od=tube_od,
                                         length=prop_hort_spread_length,
                                         end_rotation=180,
                                         name="prop_hort_tube_l",
                                         mount_base_inst=front_hub,
                                         mount_base_conn="Side_Connector_1")
    prop_hort_tube_r = designer.add_tube(od=tube_od,
                                         length=prop_hort_spread_length,
                                         end_rotation=180,
                                         name="prop_hort_tube_r",
                                         mount_base_inst=front_hub,
                                         mount_base_conn="Side_Connector_3")
    prop_hub_l = designer.add_hub(name="prop_hub_l",
                                  num_connects=2,
                                  diameter=tube_od,
                                  connector_horizonal_angle=180,
                                  connector_vertical_angle=0,
                                  connects=["Bottom_Connector"],
                                  mount_inst=[prop_hort_tube_l],
                                  mount_conn=["EndConnection"])
    prop_hub_r = designer.add_hub(name="prop_hub_r",
                                  num_connects=2,
                                  diameter=tube_od,
                                  connector_horizonal_angle=180,
                                  connector_vertical_angle=0,
                                  connects=["Top_Connector"],
                                  mount_inst=[prop_hort_tube_r],
                                  mount_conn=["EndConnection"])
    top_prop_tube_l = designer.add_tube(od=tube_od,
                                        length=prop_vert_spread_length,
                                        end_rotation=90,
                                        name="top_prop_tube_l",
                                        mount_base_inst=prop_hub_l,
                                        mount_base_conn="Side_Connector_1")
    top_prop_tube_r = designer.add_tube(od=tube_od,
                                        length=prop_vert_spread_length,
                                        end_rotation=90,
                                        name="top_prop_tube_r",
                                        mount_base_inst=prop_hub_r,
                                        mount_base_conn="Side_Connector_1")
    top_prop_flange_l = designer.add_flange(hole_diameter=tube_od,
                                            name="top_prop_flange_l",
                                            mount_side_inst=top_prop_tube_l,
                                            mount_side_conn="EndConnection"
                                            )
    designer.add_motor_propeller(motor_model=motor_type,
                                 prop_model=prop_type,
                                 prop_type=1,
                                 direction=1,
                                 control_channel=3,
                                 name_prefix="top_l",
                                 mount_inst=top_prop_flange_l,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    top_prop_flange_r = designer.add_flange(hole_diameter=tube_od,
                                            name="top_prop_flange_r",
                                            mount_side_inst=top_prop_tube_r,
                                            mount_side_conn="EndConnection"
                                            )
    designer.add_motor_propeller(motor_model=motor_type,
                                 prop_model=prop_type,
                                 prop_type=-1,
                                 direction=-1,
                                 control_channel=4,
                                 name_prefix="top_r",
                                 mount_inst=top_prop_flange_r,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    bottom_prop_tube_l = designer.add_tube(od=tube_od,
                                           length=prop_vert_spread_length,
                                           end_rotation=270,
                                           name="bottom_prop_tube_l",
                                           mount_base_inst=prop_hub_l,
                                           mount_base_conn="Side_Connector_2")
    bottom_prop_tube_r = designer.add_tube(od=tube_od,
                                           length=prop_vert_spread_length,
                                           end_rotation=270,
                                           name="bottom_prop_tube_r",
                                           mount_base_inst=prop_hub_r,
                                           mount_base_conn="Side_Connector_2")
    bottom_prop_flange_l = designer.add_flange(hole_diameter=tube_od,
                                               name="bottom_prop_flange_l",
                                               mount_side_inst=bottom_prop_tube_l,
                                               mount_side_conn="EndConnection"
                                               )
    designer.add_motor_propeller(motor_model=motor_type,
                                 prop_model=prop_type,
                                 prop_type=-1,
                                 direction=-1,
                                 control_channel=5,
                                 name_prefix="bottom_l",
                                 mount_inst=bottom_prop_flange_l,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    bottom_prop_flange_r = designer.add_flange(hole_diameter=tube_od,
                                               name="bottom_prop_flange_r",
                                               mount_side_inst=bottom_prop_tube_r,
                                               mount_side_conn="EndConnection"
                                               )
    designer.add_motor_propeller(motor_model=motor_type,
                                 prop_model=prop_type,
                                 prop_type=1,
                                 direction=1,
                                 control_channel=6,
                                 name_prefix="bottom_r",
                                 mount_inst=bottom_prop_flange_r,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)



    ########################################
    # Optional Tail


    designer.close_design(corpus="uav", orient_z_angle=180)

    study_params = {
        "Flight_Path": 9,
        "Requested_Lateral_Speed": 19,
        "Requested_Vertical_Speed": -2,
        "Requested_Vertical_Down_Speed": 2,
        "Requested_Lateral_Acceleration": 0.125,
        "Requested_Lateral_Deceleration": -0.125,
        "Requested_Vertical_Acceleration": -0.2,
        "Requested_Vertical_Deceleration": 0.2,
        # James suggested not to tweak these
        # "Landing_Approach_Height": 3,
        # "Vertical_Landing_Speed": 0.5,    # not used in buildcad.py
        # "Vertical_Landing_Speed_At_Ground": 0.1,
        "Q_Position": 1,
        "Q_Velocity": 1,
        "Q_Angular_Velocity": 1,
        "Q_Angles": 1,
        "Ctrl_R": 0.1,
    }

    # Add all study parameters automatically
    for val in locals().values():
        if isinstance(val, StudyParam):
            study_params[val.name] = val.value

    return design_name, study_params

