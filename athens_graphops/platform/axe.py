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

from ..designer import Designer, StudyParam

# FYI: wings seem to protrude into the propellers, but that
# is how it is the seed design


def create_pick_axe():
    return axe_platform("PickAxeVU", front_lower_rail=True)

# FYI: rear wings seem to protrude into the propellers, but that
# is not how it is the seed design - looked for the issue, but
# didn't find it


def create_new_axe():
    return axe_platform("NewAxeCargoVU")


def axe_platform(variant, front_lower_rail=False):
    """
    Designs with two vertical wing sets (front and rear) 
    placed horizontally and two vertical wings as rudders 
    placed vertically under the rear wings
    """
    design_name = variant

    designer = Designer()
    designer.create_design(design_name)

    ########################################
    # Static params
    battery_type = "TurnigyGraphene6000mAh6S75C"
    if front_lower_rail:
        motor_type = "t_motor_AntigravityMN4006KV380"
        propeller_type = "apc_propellers_12x3_8SF"
    else:
        motor_type = "kde_direct_KDE2315XF_885"
        propeller_type = "apc_propellers_7x5E"

    naca_profile = "0012"
    wing_thickness = 12
    tube_od = 7.1374

    body_rot_angle = 90
    angle_270 = 270

    fwd_facing_cw_prop_type = 1
    fwd_facing_ccw_prop_type = -1
    fwd_facing_cw_spin = 1
    fwd_facing_ccw_spin = -1

    front_l_wing_offset = 289.68
    front_r_wing_offset = 160.32
    rear_wing_offset = 90
    rear_l_wing_offset = 448.68
    r_rudder_offset = 50
    l_rudder_offset = 90

    # wing tube rotation (front left/right, left rudder) and mid_tube_l end rotation
    param_11 = 180
    # rear right wing TUBE_ROTATION and hub ANGHORZCONN (main, side, rear)
    param_12 = 90

    # Battery and Sensor placement
    offset_1 = -20
    offset_2 = 50
    offset_3 = 33
    offset_4 = -30
    offset_5 = -80
    offset_6 = 70
    offset_7 = -70
    offset_8 = 11
    offset_9 = -11

    ########################################
    # Tunable params
    cargo_mass = designer.set_study_param("CargoMass", [0.001, 0.5])

    fuse_floor = designer.set_study_param("fuse_floor", 20)
    fuse_width = designer.set_study_param("fuse_width", 300)
    fuse_height = designer.set_study_param("fuse_height", 105)
    if front_lower_rail:
        fuse_length = designer.set_study_param("fuse_length", 140)
        front_wing_load = designer.set_study_param("front_wing_load", 30)
        front_rail_length = designer.set_study_param("front_rail_length", 135)
    else:
        fuse_length = designer.set_study_param("fuse_length", 150)
        front_wing_load = designer.set_study_param("front_wing_load", 15)
        front_rail_length = designer.set_study_param("front_rail_length", 335)

    front_wing_tube_length = designer.set_study_param(
        "front_wing_tube_length", 52)
    front_wing_span = designer.set_study_param("front_wing_span", 450)
    front_wing_chord = designer.set_study_param("front_wing_chord", 150)

    mid_tube_length = designer.set_study_param("mid_tube_length", 140)
    top_leg_tube_length = designer.set_study_param(
        "top_leg_tube_length", 150.1524)
    rail_lower_length = designer.set_study_param("rail_lower_length", 90)
    rail_down_length = designer.set_study_param("rail_down_length", 90)
    rear_rail_length = designer.set_study_param("rear_rail_length", 220)
    vertical_tube_length = designer.set_study_param(
        "vertical_tube_length", 150)

    rear_wing_span = designer.set_study_param("rear_wing_span", 609)
    rear_wing_chord = designer.set_study_param("rear_wing_chord", 180)
    rear_wing_load = designer.set_study_param("rear_wing_load", 30)

    rudder_tube_length = designer.set_study_param("rudder_tube_length", 41)
    rudder_span = designer.set_study_param("rudder_span", 140)
    rudder_chord = designer.set_study_param("rudder_chord", 100)
    rudder_wing_load = designer.set_study_param("rudder_wing_load", 20)

    ########################################
    # Center (Hub, Fuselage, Cargo)
    fuselage = designer.add_fuselage_uav(name="fuselage",
                                         floor_height=fuse_floor,
                                         fuse_width=fuse_width,
                                         fuse_height=fuse_height,
                                         fuse_cyl_length=fuse_length,
                                         bottom_connector_rotation=body_rot_angle)
    # Setup cargo mass to represent a full cargo
    cargo_mass_list = designer.param_value(cargo_mass)
    cargo, cargo_case = designer.add_cargo(weight=cargo_mass_list[1],
                                           name="cargo")

    # Require main_hub for connection to Orient
    # Create hub connection lists (size of num_connections max)
    # Not all connections are needed
    hub_main = designer.add_hub(name="main_hub",
                                num_connects=3,
                                connector_horizonal_angle=param_12,
                                connects=["Top_Connector", "Bottom_Connector"],
                                mount_inst=[fuselage, cargo_case],
                                mount_conn=["BottomConnector",
                                            "Case2HubConnector"],
                                orient_base=True)

    ########################################
    # Batteries
    battery_control = designer.add_battery_controller(name="BatteryController")
    designer.add_battery_uav(model=battery_type,
                             name="Battery_1",
                             fuse_conn_num=2,
                             mount_length=0,
                             mount_width=offset_7,
                             controller_inst=battery_control)

    designer.add_battery_uav(model=battery_type,
                             name="Battery_2",
                             fuse_conn_num=1,
                             mount_length=0,
                             mount_width=offset_6,
                             controller_inst=battery_control)

    ########################################
    # Sensors
    designer.add_sensor(sensor_model="RpmTemp",
                        name="RpmTemp",
                        mount_conn_num=3,
                        mount_length=offset_1,
                        mount_width=offset_3)
    designer.add_sensor(sensor_model="Current",
                        name="Current",
                        mount_conn_num=4,
                        mount_length=offset_1,
                        mount_width=offset_4)
    designer.add_sensor(sensor_model="Autopilot",
                        name="Autopilot",
                        mount_conn_num=5,
                        mount_length=offset_2,
                        mount_width=0)
    designer.add_sensor(sensor_model="Voltage",
                        name="Voltage",
                        mount_conn_num=6,
                        mount_length=offset_1,
                        mount_width=offset_8)
    designer.add_sensor(sensor_model="GPS",
                        name="GPS",
                        mount_conn_num=7,
                        mount_length=offset_5,
                        mount_width=0)
    designer.add_sensor(sensor_model="Variometer",
                        name="Variometer",
                        mount_conn_num=8,
                        mount_length=offset_1,
                        mount_width=offset_9)

    ########################################
    # Create front propellers section
    # Start at main hub, connect tubes on sides to side hubs,
    # then front flange and rail attach to propellers/motors
    mid_tube_l = designer.add_tube(od=tube_od,
                                   length=mid_tube_length,
                                   end_rotation=param_11,
                                   name="mid_tube_l",
                                   mount_base_inst=hub_main,
                                   mount_base_conn="Side_Connector_3")
    mid_tube_r = designer.add_tube(od=tube_od,
                                   length=mid_tube_length,
                                   name="mid_tube_r",
                                   mount_base_inst=hub_main,
                                   mount_base_conn="Side_Connector_1")
    side_hub_l = designer.add_hub(name="side_hub_l",
                                  num_connects=3,
                                  diameter=tube_od,
                                  connector_horizonal_angle=param_12,
                                  connects=["Side_Connector_2"],
                                  mount_inst=[mid_tube_l],
                                  mount_conn=["EndConnection"])
    side_hub_r = designer.add_hub(name="side_hub_r",
                                  num_connects=3,
                                  diameter=tube_od,
                                  connector_horizonal_angle=param_12,
                                  connects=["Side_Connector_2"],
                                  mount_inst=[mid_tube_r],
                                  mount_conn=["EndConnection"])
    front_rail_l = designer.add_tube(od=tube_od,
                                     length=front_rail_length,
                                     end_rotation=angle_270,
                                     name="front_rail_l",
                                     mount_base_inst=side_hub_l,
                                     mount_base_conn="Side_Connector_3")
    front_rail_r = designer.add_tube(od=tube_od,
                                     length=front_rail_length,
                                     end_rotation=body_rot_angle,
                                     name="front_rail_r",
                                     mount_base_inst=side_hub_r,
                                     mount_base_conn="Side_Connector_3")

    if front_lower_rail:
        front_hub_l = designer.add_hub(name="front_hub_l",
                                       num_connects=4,
                                       diameter=tube_od,
                                       connector_horizonal_angle=90,
                                       connects=["Side_Connector_1"],
                                       mount_inst=[front_rail_l],
                                       mount_conn=["EndConnection"])
        front_hub_r = designer.add_hub(name="front_hub_r",
                                       num_connects=4,
                                       diameter=tube_od,
                                       connector_horizonal_angle=90,
                                       connects=["Side_Connector_1"],
                                       mount_inst=[front_rail_r],
                                       mount_conn=["EndConnection"])
        front_railDwn_l = designer.add_tube(od=tube_od,
                                            length=rail_down_length,
                                            name="front_railDwn_l",
                                            mount_base_inst=front_hub_l,
                                            mount_base_conn="Side_Connector_2")
        front_railDwn_r = designer.add_tube(od=tube_od,
                                            length=rail_down_length,
                                            name="front_railDwn_r",
                                            mount_base_inst=front_hub_r,
                                            mount_base_conn="Side_Connector_2")
        front_hubLower_l = designer.add_hub(name="front_hubLower_l",
                                            num_connects=2,
                                            diameter=tube_od,
                                            connector_horizonal_angle=angle_270,
                                            connects=["Side_Connector_1"],
                                            mount_inst=[front_railDwn_l],
                                            mount_conn=["EndConnection"])
        front_hubLower_r = designer.add_hub(name="front_hubLower_r",
                                            num_connects=2,
                                            diameter=tube_od,
                                            connector_horizonal_angle=angle_270,
                                            connects=["Side_Connector_1"],
                                            mount_inst=[front_railDwn_r],
                                            mount_conn=["EndConnection"])
        front_railLower_l = designer.add_tube(od=tube_od,
                                              length=rail_lower_length,
                                              name="front_railLower_l",
                                              mount_base_inst=front_hubLower_l,
                                              mount_base_conn="Side_Connector_2")
        front_railLower_r = designer.add_tube(od=tube_od,
                                              length=rail_lower_length,
                                              name="front_railLower_r",
                                              mount_base_inst=front_hubLower_r,
                                              mount_base_conn="Side_Connector_2")
        front_flange_l = designer.add_flange(hole_diameter=tube_od,
                                             name="front_flange_l",
                                             mount_bottom_inst=front_railLower_l,
                                             mount_bottom_conn="EndConnection"
                                             )
        front_flange_r = designer.add_flange(hole_diameter=tube_od,
                                             bottom_angle=body_rot_angle,
                                             name="front_flange_r",
                                             mount_bottom_inst=front_railLower_r,
                                             mount_bottom_conn="EndConnection"
                                             )
    # for new axe design
    else:
        front_flange_l = designer.add_flange(hole_diameter=tube_od,
                                             name="front_flange_l",
                                             mount_bottom_inst=front_rail_l,
                                             mount_bottom_conn="EndConnection"
                                             )
        front_flange_r = designer.add_flange(hole_diameter=tube_od,
                                             bottom_angle=body_rot_angle,
                                             name="front_flange_r",
                                             mount_bottom_inst=front_rail_r,
                                             mount_bottom_conn="EndConnection"
                                             )

    # Applies to pick axe and new axe designs
    designer.add_motor_propeller(motor_model=motor_type,
                                 prop_model=propeller_type,
                                 prop_type=fwd_facing_ccw_prop_type,
                                 direction=fwd_facing_ccw_spin,
                                 control_channel=1,
                                 name_prefix="front_l",
                                 mount_inst=front_flange_l,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    designer.add_motor_propeller(motor_model=motor_type,
                                 prop_model=propeller_type,
                                 prop_type=fwd_facing_cw_prop_type,
                                 direction=fwd_facing_cw_spin,
                                 control_channel=2,
                                 name_prefix="front_r",
                                 mount_inst=front_flange_r,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)

    ########################################
    # Add front wings
    front_wing_tube_l = designer.add_tube(od=tube_od,
                                          length=front_wing_tube_length,
                                          name="front_wing_tube_l",
                                          mount_base_inst=front_flange_l,
                                          mount_base_conn="SideConnector")
    front_wing_tube_r = designer.add_tube(od=tube_od,
                                          length=front_wing_tube_length,
                                          name="front_wing_tube_r",
                                          mount_base_inst=front_flange_r,
                                          mount_base_conn="SideConnector")
    # Note: the autograph for the seed design indicates a tube_rotation of 180 for left wing, 90 looks more correct (MM)
    designer.add_wing_uav(direction="Vertical",
                          chord=front_wing_chord,
                          span=front_wing_span,
                          thickness=wing_thickness,
                          naca=naca_profile,
                          load=front_wing_load,
                          tube_diameter=tube_od,
                          tube_offset=front_l_wing_offset,
                          tube_rotation=param_11,
                          channel=5,
                          name="front_left_wing",
                          tube_inst=front_wing_tube_l,
                          tube_conn="EndConnection")
    designer.add_wing_uav(direction="Vertical",
                          chord=front_wing_chord,
                          span=front_wing_span,
                          thickness=wing_thickness,
                          naca=naca_profile,
                          load=front_wing_load,
                          tube_diameter=tube_od,
                          tube_offset=front_r_wing_offset,
                          tube_rotation=param_11,
                          channel=6,
                          name="front_right_wing",
                          tube_inst=front_wing_tube_r,
                          tube_conn="EndConnection")

    ########################################
    # Add rear wings
    rear_rail_l = designer.add_tube(od=tube_od,
                                    length=rear_rail_length,
                                    end_rotation=body_rot_angle,
                                    name="rear_rail_l",
                                    mount_base_inst=side_hub_l,
                                    mount_base_conn="Side_Connector_1")
    rear_rail_r = designer.add_tube(od=tube_od,
                                    length=rear_rail_length,
                                    end_rotation=body_rot_angle,
                                    name="rear_rail_r",
                                    mount_base_inst=side_hub_r,
                                    mount_base_conn="Side_Connector_1")
    rear_hub_l = designer.add_hub(name="rear_hub_l",
                                  num_connects=3,
                                  diameter=tube_od,
                                  connector_horizonal_angle=param_12,
                                  connects=["Side_Connector_1"],
                                  mount_inst=[rear_rail_l],
                                  mount_conn=["EndConnection"])
    rear_hub_r = designer.add_hub(name="rear_hub_r",
                                  num_connects=3,
                                  diameter=tube_od,
                                  connector_horizonal_angle=param_12,
                                  connects=["Side_Connector_3"],
                                  mount_inst=[rear_rail_r],
                                  mount_conn=["EndConnection"])
    bottom_leg_l = designer.add_tube(od=tube_od,
                                     length=vertical_tube_length,
                                     name="bottom_leg_l",
                                     mount_base_inst=rear_hub_l,
                                     mount_base_conn="Side_Connector_3")
    bottom_leg_r = designer.add_tube(od=tube_od,
                                     length=vertical_tube_length,
                                     name="bottom_leg_r",
                                     mount_base_inst=rear_hub_r,
                                     mount_base_conn="Side_Connector_1")
    vertical_l = designer.add_tube(od=tube_od,
                                   length=vertical_tube_length,
                                   end_rotation=body_rot_angle,
                                   offset_1=rear_wing_offset,
                                   name="vertical_l",
                                   mount_base_inst=rear_hub_l,
                                   mount_base_conn="Side_Connector_2")
    vertical_r = designer.add_tube(od=tube_od,
                                   length=vertical_tube_length,
                                   end_rotation=angle_270,
                                   offset_1=rear_wing_offset,
                                   name="vertical_r",
                                   mount_base_inst=rear_hub_r,
                                   mount_base_conn="Side_Connector_2")
    designer.add_wing_uav(direction="Vertical",
                          chord=rear_wing_chord,
                          span=rear_wing_span,
                          thickness=wing_thickness,
                          naca=naca_profile,
                          load=rear_wing_load,
                          tube_diameter=tube_od,
                          tube_offset=rear_l_wing_offset,
                          tube_rotation=angle_270,
                          channel=8,
                          name="rear_left_wing",
                          tube_inst=vertical_l,
                          tube_conn="OffsetConnection1")
    designer.add_wing_uav(direction="Vertical",
                          chord=rear_wing_chord,
                          span=rear_wing_span,
                          thickness=wing_thickness,
                          naca=naca_profile,
                          load=rear_wing_load,
                          tube_diameter=tube_od,
                          tube_offset=front_r_wing_offset,
                          tube_rotation=param_12,
                          channel=7,
                          name="rear_right_wing",
                          tube_inst=vertical_r,
                          tube_conn="OffsetConnection1")
    rear_flange_l = designer.add_flange(hole_diameter=tube_od,
                                        name="rear_flange_l",
                                        mount_side_inst=vertical_l,
                                        mount_side_conn="EndConnection"
                                        )
    rear_flange_r = designer.add_flange(hole_diameter=tube_od,
                                        name="rear_flange_r",
                                        mount_side_inst=vertical_r,
                                        mount_side_conn="EndConnection"
                                        )
    designer.add_motor_propeller(motor_model=motor_type,
                                 prop_model=propeller_type,
                                 prop_type=fwd_facing_ccw_prop_type,
                                 direction=fwd_facing_ccw_spin,
                                 control_channel=3,
                                 name_prefix="rear_l",
                                 mount_inst=rear_flange_l,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    designer.add_motor_propeller(motor_model=motor_type,
                                 prop_model=propeller_type,
                                 prop_type=fwd_facing_cw_prop_type,
                                 direction=fwd_facing_cw_spin,
                                 control_channel=4,
                                 name_prefix="rear_r",
                                 mount_inst=rear_flange_r,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    top_leg_l = designer.add_tube(od=tube_od,
                                  length=top_leg_tube_length,
                                  name="top_leg_l",
                                  mount_base_inst=rear_flange_l,
                                  mount_base_conn="BottomConnector")
    top_leg_r = designer.add_tube(od=tube_od,
                                  length=top_leg_tube_length,
                                  name="top_leg_r",
                                  mount_base_inst=rear_flange_r,
                                  mount_base_conn="BottomConnector")

    ########################################
    # Add rudders
    rudder_tube_l = designer.add_tube(od=tube_od,
                                      length=rudder_tube_length,
                                      name="rudder_tube_l",
                                      mount_base_inst=rear_hub_l,
                                      mount_base_conn="Center_Connector")
    rudder_tube_r = designer.add_tube(od=tube_od,
                                      length=rudder_tube_length,
                                      name="rudder_tube_r",
                                      mount_base_inst=rear_hub_r,
                                      mount_base_conn="Center_Connector")
    designer.add_wing_uav(direction="Vertical",
                          chord=rudder_chord,
                          span=rudder_span,
                          thickness=wing_thickness,
                          naca=naca_profile,
                          load=rudder_wing_load,
                          tube_diameter=tube_od,
                          tube_offset=l_rudder_offset,
                          tube_rotation=param_11,
                          channel=10,
                          name="left_rudder",
                          tube_inst=rudder_tube_l,
                          tube_conn="EndConnection")
    designer.add_wing_uav(direction="Vertical",
                          chord=rudder_chord,
                          span=rudder_span,
                          thickness=wing_thickness,
                          naca=naca_profile,
                          load=rudder_wing_load,
                          tube_diameter=tube_od,
                          tube_offset=r_rudder_offset,
                          channel=9,
                          name="right_rudder",
                          tube_inst=rudder_tube_r,
                          tube_conn="EndConnection")

    designer.close_design(corpus="uav", orient_z_angle=body_rot_angle)

    study_params = {
        "Flight_Path": 9,
        "Requested_Lateral_Speed": 23,
        "Requested_Vertical_Speed": -5,
        "Requested_Vertical_Down_Speed": 5,
        "Requested_Lateral_Acceleration": 2,
        "Requested_Lateral_Deceleration": -3,
        "Requested_Vertical_Acceleration": -1,
        "Requested_Vertical_Deceleration": 1,
        # James suggested not to tweak these
        # "Landing_Approach_Height": 3,
        # "Vertical_Landing_Speed": 0.5,    # not used in buildcad.py
        # "Vertical_Landing_Speed_At_Ground": 0.1,
        "Q_Position": 0.158489319,
        "Q_Velocity": 0.0158489319,
        "Q_Angular_Velocity": 0.501187234,
        "Q_Angles": 0.01,
        "Ctrl_R": 0.316227766,
    }

    # Add all study parameters automatically
    for val in locals().values():
        if isinstance(val, StudyParam):
            study_params[val.name] = val.value

    return design_name, study_params
