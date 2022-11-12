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
from ..designer2 import Designer, StudyParam


def create_falcon_t():
    return falcon_t_platform("")


def create_falcon_t_with_tail():
    return falcon_t_platform("WithTail", with_tail=True)


def falcon_t_platform(variant, with_tail=False):
    """
    Create a minimal design (does not include uam_direct2cad workflow at this time,
    it only creates the graph design).
    """
    design_name = "FalconT" + variant

    designer = Designer()
    designer.create_design(design_name)

    # tuneable parameters
    tube_od = 7.1374  # cannot be a study param (fixed CAD models)

    wing_span = designer.set_study_param("wing_span", 600)

    # extra space (50mm) around the fuselage
    wing_tube_length = designer.set_study_param(
        "wing_tube_length", designer.param_value(wing_span) + 50
    )

    wing_chord = designer.set_study_param("wing_chord", 100)

    # the two wings need to carry about 5kg (50 N) weight
    wing_load = designer.set_study_param("wing_load", 25)

    # distance of the motor plane from the wing root
    forward_tube_length = designer.set_study_param("forward_tube_length", 200)

    # width of the motors
    front_horiz_tube_length = designer.set_study_param(
        "front_horiz_tube_length", 200
    )

    # height of the top motors
    front_vert_upper_tube_length = designer.set_study_param(
        "front_vert_upper_tube_length", 200
    )

    # depth of the bottom motors
    front_vert_lower_tube_length = designer.set_study_param(
        "front_vert_lower_tube_length", 200
    )

    cargo_mass = designer.set_study_param("cargo_mass", 0.5)

    ########################################
    # Center (Hun, Fuselage, Cargo)
    fuselage = designer.add_fuselage(
        name="fuselage",
        floor_height=20,
        fuse_width=190,
        fuse_height=125,
        fuse_cyl_length=270,
        bottom_connector_rotation=90,
    )
    cargo, cargo_case = designer.add_cargo(weight=cargo_mass, name="cargo")  # type: ignore

    # Require main_hub for connection to Orient
    # Create hub connection lists (size of num_connections max)
    # Not all connections are needed
    main_hub = designer.add_hub(
        name="main_hub",
        diameter=tube_od,
        num_connects=4,
        connector_horizonal_angle=90,
        connects=["Top_Connector", "Bottom_Connector"],
        mount_inst=[fuselage, cargo_case],
        mount_conn=["BottomConnector", "Case2HubConnector"],
        orient_base=True,
    )

    ########################################
    # Batteries
    battery_control = designer.add_battery_controller(name="BatteryController")
    designer.add_battery(
        name="Battery_1",
        model="TurnigyGraphene6000mAh6S75C",
        fuse_conn_num=1,
        mount_length=0,
        mount_width=30,
        controller_inst=battery_control,
    )

    designer.add_battery(
        name="Battery_2",
        model="TurnigyGraphene6000mAh6S75C",
        fuse_conn_num=2,
        mount_length=0,
        mount_width=-30,
        controller_inst=battery_control,
    )

    ########################################
    # Sensors
    designer.add_sensor(
        name="RpmTemp",
        sensor_model="RpmTemp",
        mount_conn_num=3,
        rotation=90,
        mount_length=-160,
        mount_width=13,
    )
    designer.add_sensor(
        name="Current",
        sensor_model="Current",
        mount_conn_num=4,
        rotation=90,
        mount_length=-160,
        mount_width=-18,
    )
    designer.add_sensor(
        name="Autopilot",
        sensor_model="Autopilot",
        mount_conn_num=5,
        rotation=90,
        mount_length=115,
        mount_width=0,
    )
    designer.add_sensor(
        name="Voltage",
        sensor_model="Voltage",
        mount_conn_num=6,
        rotation=90,
        mount_length=155,
        mount_width=18,
    )
    designer.add_sensor(
        name="GPS",
        sensor_model="GPS",
        mount_conn_num=7,
        mount_length=-120,
        mount_width=0,
    )
    designer.add_sensor(
        name="Variometer",
        sensor_model="Variometer",
        mount_conn_num=8,
        rotation=90,
        mount_length=155,
        mount_width=-18,
    )

    ########################################
    # Wings
    wing_tube_r = designer.add_tube(
        name="wing_tube_r",
        od=tube_od,
        length=wing_tube_length,
        offset_1=wing_tube_length,  # type: ignore
        mount_base_inst=main_hub,
        mount_base_conn="Side_Connector_1",
    )

    wing_tube_l = designer.add_tube(
        name="wing_tube_l",
        od=tube_od,
        length=wing_tube_length,
        offset_1=wing_tube_length,  # type: ignore
        mount_base_inst=main_hub,
        mount_base_conn="Side_Connector_3",
    )

    wing_r = designer.add_wing(
        name="wing_r",
        direction="Horizontal",
        chord=wing_chord,
        span=wing_span,
        thickness=12,
        naca="0012",
        load=wing_load,  # type: ignore
        tube_diameter=tube_od,
        tube_rotation=270,
        channel=5,
        flap_bias=0.0,
        aileron_bias=1.0,
        tube_inst=wing_tube_r,
        tube_conn="OffsetConnection1",
    )

    wing_l = designer.add_wing(
        name="wing_l",
        direction="Horizontal",
        chord=wing_chord,
        span=wing_span,
        thickness=12,
        naca="0012",
        load=wing_load,  # type: ignore
        tube_diameter=tube_od,
        tube_rotation=90,
        channel=6,
        flap_bias=0.0,
        aileron_bias=-1.0,
        tube_inst=wing_tube_l,
        tube_conn="OffsetConnection1",
    )

    ########################################
    # Forward structure
    forward_tube = designer.add_tube(
        name="forward_tube",
        od=tube_od,
        length=forward_tube_length,
        mount_base_inst=main_hub,
        mount_base_conn="Side_Connector_4",
    )

    forward_hub = designer.add_hub(
        name="forward_hub",
        diameter=tube_od,
        num_connects=3,
        connector_horizonal_angle=90,
        connects=["Side_Connector_2"],
        mount_inst=[forward_tube],
        mount_conn=["EndConnection"],
    )

    front_horiz_tube_r = designer.add_tube(
        name="front_horiz_tube_r",
        od=tube_od,
        length=front_horiz_tube_length,
        end_rotation=90,
        mount_base_inst=forward_hub,
        mount_base_conn="Side_Connector_1",
    )

    front_horiz_tube_l = designer.add_tube(
        name="front_horiz_tube_l",
        od=tube_od,
        length=front_horiz_tube_length,
        end_rotation=90,
        mount_base_inst=forward_hub,
        mount_base_conn="Side_Connector_3",
    )

    front_hub_r = designer.add_hub(
        name="front_hub_r",
        diameter=tube_od,
        num_connects=3,
        connector_horizonal_angle=90,
        connects=["Side_Connector_2"],
        mount_inst=[front_horiz_tube_r],
        mount_conn=["EndConnection"],
    )

    front_hub_l = designer.add_hub(
        name="front_hub_l",
        diameter=tube_od,
        num_connects=3,
        connector_horizonal_angle=90,
        connects=["Side_Connector_2"],
        mount_inst=[front_horiz_tube_l],
        mount_conn=["EndConnection"],
    )

    front_vert_upper_tube_r = designer.add_tube(
        name="front_vert_upper_tube_r",
        od=tube_od,
        length=front_vert_upper_tube_length,
        mount_base_inst=front_hub_r,
        mount_base_conn="Side_Connector_1",
    )

    front_vert_lower_tube_r = designer.add_tube(
        name="front_vert_lower_tube_r",
        od=tube_od,
        length=front_vert_lower_tube_length,
        mount_base_inst=front_hub_r,
        mount_base_conn="Side_Connector_3",
    )

    front_vert_upper_tube_l = designer.add_tube(
        name="front_vert_upper_tube_l",
        od=tube_od,
        length=front_vert_upper_tube_length,
        end_rotation=180,
        mount_base_inst=front_hub_l,
        mount_base_conn="Side_Connector_1",
    )

    front_vert_lower_tube_l = designer.add_tube(
        name="front_vert_lower_tube_l",
        od=tube_od,
        length=front_vert_lower_tube_length,
        end_rotation=180,
        mount_base_inst=front_hub_l,
        mount_base_conn="Side_Connector_3",
    )

    ########################################
    # Motors
    front_flange_upper_r = designer.add_flange(
        name="front_flange_upper_r",
        hole_diameter=tube_od,
        mount_side_inst=front_vert_upper_tube_r,
        mount_side_conn="EndConnection",
    )

    front_flange_lower_r = designer.add_flange(
        name="front_flange_lower_r",
        hole_diameter=tube_od,
        mount_side_inst=front_vert_lower_tube_r,
        mount_side_conn="EndConnection",
    )

    front_flange_upper_l = designer.add_flange(
        name="front_flange_upper_l",
        hole_diameter=tube_od,
        mount_side_inst=front_vert_upper_tube_l,
        mount_side_conn="EndConnection",
    )

    front_flange_lower_l = designer.add_flange(
        name="front_flange_lower_l",
        hole_diameter=tube_od,
        mount_side_inst=front_vert_lower_tube_l,
        mount_side_conn="EndConnection",
    )

    # TODO: triple check prop_type and direction for all motors
    designer.add_motor_propeller(
        name_prefix="front_upper_r",
        motor_model="t_motor_AntigravityMN4006KV380",
        prop_model="apc_propellers_12x3_8SF",
        prop_type=-1,
        direction=-1,
        control_channel=1,
        mount_inst=front_flange_upper_r,
        mount_conn="TopConnector",
        controller_inst=battery_control,
    )

    designer.add_motor_propeller(
        name_prefix="front_lower_r",
        motor_model="t_motor_AntigravityMN4006KV380",
        prop_model="apc_propellers_12x3_8SF",
        prop_type=1,
        direction=1,
        control_channel=2,
        mount_inst=front_flange_lower_r,
        mount_conn="TopConnector",
        controller_inst=battery_control,
    )

    designer.add_motor_propeller(
        name_prefix="front_upper_l",
        motor_model="t_motor_AntigravityMN4006KV380",
        prop_model="apc_propellers_12x3_8SF",
        prop_type=1,
        direction=1,
        control_channel=3,
        mount_inst=front_flange_upper_l,
        mount_conn="TopConnector",
        controller_inst=battery_control,
    )

    designer.add_motor_propeller(
        name_prefix="front_lower_l",
        motor_model="t_motor_AntigravityMN4006KV380",
        prop_model="apc_propellers_12x3_8SF",
        prop_type=-1,
        direction=-1,
        control_channel=4,
        mount_inst=front_flange_lower_l,
        mount_conn="TopConnector",
        controller_inst=battery_control,
    )

    ########################################
    # Optional Tail
    if with_tail:

        rearward_tube_length = designer.set_study_param(
            "rearward_tube_length", 250
        )
        rudder_span = designer.set_study_param("rudder_span", 200)
        rudder_chord = designer.set_study_param("rudder_chord", 100)
        rudder_load = designer.set_study_param("rudder_load", 5)
        rudder_tube_length = designer.set_study_param(
            "rudder_tube_length", designer.param_value(rudder_span) + 25
        )

        rearward_tube = designer.add_tube(
            name="rearward_tube",
            od=tube_od,
            length=rearward_tube_length,
            mount_base_inst=main_hub,
            end_rotation=270,
            mount_base_conn="Side_Connector_2",
        )

        rearward_hub = designer.add_hub(
            name="rearward_hub",
            diameter=tube_od,
            num_connects=2,
            connector_horizonal_angle=90,
            connects=["Side_Connector_1"],
            mount_inst=[rearward_tube],
            mount_conn=["EndConnection"],
        )

        rudder_tube = designer.add_tube(
            name="rudder_tube",
            od=tube_od,
            length=rudder_tube_length,
            mount_base_inst=rearward_hub,
            mount_base_conn="Side_Connector_2",
            offset_1=rudder_tube_length,  # type: ignore
        )

        rudder = designer.add_wing(
            name="rudder",
            direction="Horizontal",
            chord=rudder_chord,
            span=rudder_span,
            thickness=12,
            naca="0012",
            load=rudder_load,  # type: ignore
            tube_diameter=tube_od,
            tube_rotation=270,
            channel=7,
            flap_bias=0.0,
            aileron_bias=1.0,
            tube_inst=rudder_tube,
            tube_conn="OffsetConnection1",
        )

    designer.close_design(orient_z_angle=90)

    study_params = {
        "Flight_Path": 9,
        "Requested_Vertical_Speed": -1,
        "Requested_Lateral_Speed": 16,
        "Requested_Vertical_Down_Speed": 1,
        "Requested_Lateral_Acceleration": 2,
        "Requested_Lateral_Deceleration": -5,
        "Requested_Vertical_Acceleration": -5,
        "Requested_Vertical_Deceleration": 5,
        # James suggested not to tweak these
        # "Landing_Approach_Height": 3,
        # "Vertical_Landing_Speed": 0.5,    # not used in buildcad.py
        # "Vertical_Landing_Speed_at_Ground": 0.1,
        "Q_Position": 1,
        "Q_Velocity": 0.5,
        "Q_Angular_Velocity": 1,
        "Q_Angles": 0.5,
        "Ctrl_R": 0.25,
    }

    # Add all study parameters automatically
    for val in locals().values():
        if isinstance(val, StudyParam):
            study_params[val.name] = val.value

    return design_name, study_params
