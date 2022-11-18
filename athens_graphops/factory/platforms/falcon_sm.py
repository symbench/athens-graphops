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

from ..workbench import Designer, StudyParam
from .. import sweep_study_param


def create_falcon_sm4():
    design_name, study_params = falcon_sm_platform("4", n_quads=1)

    # Model-specific tweaks - needs different loaded/unloaded speeds
    study_params = {
        **study_params,
        "CargoMass": [0.5, 0.001],
        "Flight_Path": 9,
        "Requested_Lateral_Speed": 32,
        "Requested_Vertical_Speed": [-8, -7],
        "Requested_Vertical_Down_Speed": [19, 13],
        "Requested_Lateral_Acceleration": 2,
        "Requested_Lateral_Deceleration": [-9, -6],
        "Requested_Vertical_Acceleration": -6,
        "Requested_Vertical_Deceleration": 15,
        # James suggested not to tweak these
        # "Landing_Approach_Height": 3,
        # "Vertical_Landing_Speed": 0.5,    # not used in buildcad.py
        # "Vertical_Landing_Speed_at_Ground": 0.1,
        "Q_Position": 0.039810717,
        "Q_Velocity": 0.001995262,
        "Q_Angular_Velocity": 0.630957345,
        "Q_Angles": 0.002511886,
        "Ctrl_R": 1.584893192,
    }

    return design_name, study_params


def create_falcon_sm4_rotated():
    design_name, study_params = falcon_sm_platform(
        "4Rotated", n_quads=1, cargo_rotation=135.5
    )

    # Model-specific tweaks
    study_params = {
        **study_params,
        "CargoMass": [0.5, 0.001],
        "Flight_Path": 9,
        "Requested_Lateral_Speed": [40, 37],
        "Requested_Vertical_Speed": [-12, -18.5],
        "Requested_Vertical_Down_Speed": [14, 16],
        "Requested_Lateral_Acceleration": [5, 6],
        "Requested_Lateral_Deceleration": [-7, -9],
        "Requested_Vertical_Acceleration": [-6, -13.5],
        "Requested_Vertical_Deceleration": [14, 20.5],
        # James suggested not to tweak these, but we do
        "Landing_Approach_Height": 1.5,
        # "Vertical_Landing_Speed": 0.5,    # not used in buildcad.py
        "Vertical_Landing_Speed_at_Ground": 0.05,
        "Q_Position": [0.009999999986096776, 0.01995262312194822],
        "Q_Velocity": [0.03162277160976345, 0.31622771609763467],
        "Q_Angular_Velocity": [3.1622776627735836, 7.943282353786793],
        "Q_Angles": [0.003981071021638376, 0.00019952619722086366],
        "Ctrl_R": [1.9952623143883719, 3.162277659248337],
    }

    return design_name, study_params


def falcon_sm_platform(variant, n_quads=1, cargo_rotation=0.0):
    """
    Create a minimal design (does not include uam_direct2cad workflow at this time,
    it only creates the graph design).
    """
    design_name = "FalconSM" + variant

    designer = Designer()
    designer.create_design(design_name)

    ########################################
    # Static params
    tube_od = 7.1374  # cannot be a study param (fixed CAD models)
    motor_type = "t_motor_AntigravityMN6007IIKV320"
    prop_type = "apc_propellers_13x14"
    battery_type = "Tattu25C23000mAh6S1PHV"

    ########################################
    # Tunable params
    wing_span = designer.set_study_param("wing_span", 390)
    # extra space (50mm) around the fuselage
    wing_tube_length = designer.set_study_param(
        "wing_tube_length", designer.param_value(wing_span) + 50
    )
    wing_chord = designer.set_study_param("wing_chord", 55)
    wing_load = designer.set_study_param("wing_load", 50)

    # distance of the motor plane from the wing root
    forward_tube_length = designer.set_study_param("forward_tube_length", 100)
    # horizontal separation between the motors
    motor_horiz_distance = designer.set_study_param(
        "motor_horiz_distance", 400
    )
    motor_horiz_center_distance = designer.set_study_param(
        "motor_horiz_center_distance",
        designer.param_value(motor_horiz_distance) // 2,
    )
    # vertical height of the top row of motors
    motor_vert_height = designer.set_study_param("motor_vert_height", 150)
    # vertical depth of the bottom row of motors
    motor_vert_depth = designer.set_study_param("motor_vert_depth", 250)
    cargo_mass = designer.set_study_param("CargoMass", 0.5)

    ########################################
    # Center (Hun, Fuselage, Cargo)
    fuselage = designer.add_fuselage(
        name="fuselage",
        floor_height=14,
        fuse_width=112,
        fuse_height=125,
        fuse_cyl_length=368,
        bottom_connector_offset_length=50,
        bottom_connector_rotation=90,
    )

    cargo, cargo_case = designer.add_cargo(
        weight=cargo_mass, name="cargo", rotation=cargo_rotation  # type: ignore
    )

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
        model=battery_type,
        fuse_conn_num=1,
        mount_length=0,
        mount_width=0,
        controller_inst=battery_control,
    )

    ########################################
    # Sensors
    designer.add_sensor(
        name="RpmTemp",
        sensor_model="RpmTemp",
        mount_conn_num=3,
        rotation=90,
        mount_length=-180,
        mount_width=16,
    )
    designer.add_sensor(
        name="Current",
        sensor_model="Current",
        mount_conn_num=4,
        rotation=90,
        mount_length=-180,
        mount_width=-15,
    )
    designer.add_sensor(
        name="Autopilot",
        sensor_model="Autopilot",
        mount_conn_num=5,
        rotation=0,
        mount_length=147,
        mount_width=0,
    )
    designer.add_sensor(
        name="Voltage",
        sensor_model="Voltage",
        mount_conn_num=6,
        rotation=90,
        mount_length=-202,
        mount_width=0,
    )
    designer.add_sensor(
        name="GPS",
        sensor_model="GPS",
        mount_conn_num=7,
        mount_length=-140,
        mount_width=0,
    )
    designer.add_sensor(
        name="Variometer",
        sensor_model="Variometer",
        mount_conn_num=8,
        rotation=90,
        mount_length=199,
        mount_width=0,
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

    horiz_anchor_r = (forward_hub, "Side_Connector_1")
    horiz_anchor_l = (forward_hub, "Side_Connector_3")

    for i_quad in range(1, n_quads + 1):
        front_horiz_tube_r = designer.add_tube(
            name=f"front_horiz_tube_r{i_quad}",
            od=tube_od,
            length=(
                motor_horiz_center_distance
                if i_quad == 1
                else motor_horiz_distance
            ),
            base_rotation=270 if i_quad == 1 else 0,
            mount_base_inst=horiz_anchor_r[0],
            mount_base_conn=horiz_anchor_r[1],
        )

        front_horiz_tube_l = designer.add_tube(
            name=f"front_horiz_tube_l{i_quad}",
            od=tube_od,
            length=(
                motor_horiz_center_distance
                if i_quad == 1
                else motor_horiz_distance
            ),
            base_rotation=270 if i_quad == 1 else 0,
            mount_base_inst=horiz_anchor_l[0],
            mount_base_conn=horiz_anchor_l[1],
        )

        front_hub_r = designer.add_hub(
            name=f"front_hub_r{i_quad}",
            diameter=tube_od,
            num_connects=3 if i_quad == n_quads else 4,
            connector_horizonal_angle=90,
            connects=["Side_Connector_2"],
            mount_inst=[front_horiz_tube_r],
            mount_conn=["EndConnection"],
        )
        horiz_anchor_r = (front_hub_r, "Side_Connector_4")

        front_hub_l = designer.add_hub(
            name=f"front_hub_l{i_quad}",
            diameter=tube_od,
            num_connects=3 if i_quad == n_quads else 4,
            connector_horizonal_angle=90,
            connects=["Side_Connector_2"],
            mount_inst=[front_horiz_tube_l],
            mount_conn=["EndConnection"],
        )
        horiz_anchor_l = (front_hub_l, "Side_Connector_4")

        front_vert_upper_tube_r = designer.add_tube(
            name=f"front_vert_upper_tube_r{i_quad}",
            od=tube_od,
            length=motor_vert_height,
            mount_base_inst=front_hub_r,
            mount_base_conn="Side_Connector_1",
        )

        front_vert_lower_tube_r = designer.add_tube(
            name=f"front_vert_lower_tube_r{i_quad}",
            od=tube_od,
            length=motor_vert_depth,
            mount_base_inst=front_hub_r,
            mount_base_conn="Side_Connector_3",
        )

        front_vert_upper_tube_l = designer.add_tube(
            name=f"front_vert_upper_tube_l{i_quad}",
            od=tube_od,
            length=motor_vert_height,
            end_rotation=180,
            mount_base_inst=front_hub_l,
            mount_base_conn="Side_Connector_1",
        )

        front_vert_lower_tube_l = designer.add_tube(
            name=f"front_vert_lower_tube_l{i_quad}",
            od=tube_od,
            length=motor_vert_depth,
            end_rotation=180,
            mount_base_inst=front_hub_l,
            mount_base_conn="Side_Connector_3",
        )

        ########################################
        # Motors
        front_flange_upper_r = designer.add_flange(
            name=f"front_flange_upper_r{i_quad}",
            hole_diameter=tube_od,
            mount_side_inst=front_vert_upper_tube_r,
            mount_side_conn="EndConnection",
        )

        front_flange_lower_r = designer.add_flange(
            name=f"front_flange_lower_r{i_quad}",
            hole_diameter=tube_od,
            mount_side_inst=front_vert_lower_tube_r,
            mount_side_conn="EndConnection",
        )

        front_flange_upper_l = designer.add_flange(
            name=f"front_flange_upper_l{i_quad}",
            hole_diameter=tube_od,
            mount_side_inst=front_vert_upper_tube_l,
            mount_side_conn="EndConnection",
        )

        front_flange_lower_l = designer.add_flange(
            name=f"front_flange_lower_l{i_quad}",
            hole_diameter=tube_od,
            mount_side_inst=front_vert_lower_tube_l,
            mount_side_conn="EndConnection",
        )

        # TODO: triple check prop_type and direction for all motors
        designer.add_motor_propeller(
            name_prefix=f"front_upper_r{i_quad}",
            motor_model=motor_type,
            prop_model=prop_type,
            prop_type=-1,
            direction=-1,
            control_channel=1,
            mount_inst=front_flange_upper_r,
            mount_conn="TopConnector",
            controller_inst=battery_control,
        )

        designer.add_motor_propeller(
            name_prefix=f"front_lower_r{i_quad}",
            motor_model=motor_type,
            prop_model=prop_type,
            prop_type=1,
            direction=1,
            control_channel=2,
            mount_inst=front_flange_lower_r,
            mount_conn="TopConnector",
            controller_inst=battery_control,
        )

        designer.add_motor_propeller(
            name_prefix=f"front_upper_l{i_quad}",
            motor_model=motor_type,
            prop_model=prop_type,
            prop_type=1,
            direction=1,
            control_channel=3,
            mount_inst=front_flange_upper_l,
            mount_conn="TopConnector",
            controller_inst=battery_control,
        )

        designer.add_motor_propeller(
            name_prefix=f"front_lower_l{i_quad}",
            motor_model=motor_type,
            prop_model=prop_type,
            prop_type=-1,
            direction=-1,
            control_channel=4,
            mount_inst=front_flange_lower_l,
            mount_conn="TopConnector",
            controller_inst=battery_control,
        )

    designer.close_design(orient_z_angle=90)

    study_params = {
        "Flight_Path": 9,
        "Requested_Lateral_Speed": 32,
        "Requested_Vertical_Speed": -8,
        "Requested_Vertical_Down_Speed": 19,
        "Requested_Lateral_Acceleration": 2,
        "Requested_Lateral_Deceleration": -9,
        "Requested_Vertical_Acceleration": -6,
        "Requested_Vertical_Deceleration": 15,
        # James suggested not to tweak these
        # "Landing_Approach_Height": 3,
        # "Vertical_Landing_Speed": 0.5,    # not used in buildcad.py
        # "Vertical_Landing_Speed_at_Ground": 0.1,
        "Q_Position": 0.039810717,
        "Q_Velocity": 0.001995262,
        "Q_Angular_Velocity": 0.630957345,
        "Q_Angles": 0.002511886,
        "Ctrl_R": 1.584893192,
    }

    for val in locals().values():
        if isinstance(val, StudyParam):
            study_params[val.name] = val.value

    # study_params = sweep_study_param(study_params,
    #                                  cargo_mass.name, [0.5, 0.001])

    # study_params = sweep_study_param(
    #     study_params, wing_span.name, [360, 365, 370, 375, 380]
    # )
    # study_params = sweep_study_param(
    #     study_params, wing_chord.name, [55, 60, 65, 70]
    # )
    # study_params = sweep_study_param(
    #     study_params, forward_tube_length.name, [85, 90, 95]
    # )
    # study_params = sweep_study_param(
    #     study_params,
    #     motor_horiz_center_distance.name,
    #     [200, 205, 210, 215, 220],
    # )

    return design_name, study_params
