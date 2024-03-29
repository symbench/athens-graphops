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


def create_falcon_s4():
    design_name, description, corpus_type, study_params = falcon_s_platform(
        "4", n_quads=1, include_fdm=False
    )

    # Model-specific tweaks - needs different loaded/unloaded speeds
    study_params = [
        *study_params,
        StudyParam("Flight_Path", 9, "FDM"),
        StudyParam("Requested_Lateral_Speed", 32, "FDM"),
        StudyParam("Requested_Vertical_Speed", [-8, -7], "FDM"),
        StudyParam("Requested_Vertical_Down_Speed", [19, 13], "FDM"),
        StudyParam("Requested_Lateral_Acceleration", 2, "FDM"),
        StudyParam("Requested_Lateral_Deceleration", [-9, -6], "FDM"),
        StudyParam("Requested_Vertical_Acceleration", -6, "FDM"),
        StudyParam("Requested_Vertical_Deceleration", 15, "FDM"),
        # James suggested not to tweak these
        # StudyParam("Landing_Approach_Height", 3, "FDM"),
        # StudyParam("Vertical_Landing_Speed", 0.5, "FDM"),    # not used in buildcad.py
        # StudyParam("Vertical_Landing_Speed_At_Ground", 0.1, "FDM"),
        StudyParam("Q_Position", 0.039810717, "FDM"),
        StudyParam("Q_Velocity", 0.001995262, "FDM"),
        StudyParam("Q_Angular_Velocity", 0.630957345, "FDM"),
        StudyParam("Q_Angles", 0.002511886, "FDM"),
        StudyParam("Ctrl_R", 1.584893192, "FDM"),
    ]

    return design_name, description, corpus_type, study_params


def create_falcon_s4_rotated():
    design_name, description, corpus_type, study_params = falcon_s_platform(
        "4RotatedCargoCase", n_quads=1, cargo_rotation=135.5, include_fdm=False
    )

    # Model-specific tweaks
    study_params = [
        *study_params,
        StudyParam("Flight_Path", 9, "FDM"),
        StudyParam("Requested_Lateral_Speed", 36, "FDM"),
        StudyParam("Requested_Vertical_Speed", [-8.5, -11], "FDM"),
        StudyParam("Requested_Vertical_Down_Speed", [12.5, 9], "FDM"),
        StudyParam("Requested_Lateral_Acceleration", [4.5, 2], "FDM"),
        StudyParam("Requested_Lateral_Deceleration", [-6, -4], "FDM"),
        StudyParam("Requested_Vertical_Acceleration", [-8, -12], "FDM"),
        StudyParam("Requested_Vertical_Deceleration", [6, 10], "FDM"),
        # James suggested not to tweak these
        # StudyParam("Landing_Approach_Height", 3, "FDM"),
        # StudyParam("Vertical_Landing_Speed", 0.5, "FDM"),    # not used in buildcad.py
        # StudyParam("Vertical_Landing_Speed_At_Ground", 0.1, "FDM"),
        StudyParam("Q_Position", 0.006309573436029592, "FDM"),
        StudyParam("Q_Velocity", 0.012589252130622394, "FDM"),
        StudyParam("Q_Angular_Velocity", 1.584893193766809, "FDM"),
        StudyParam("Q_Angles", 0.0015848929201969747, "FDM"),
        StudyParam("Ctrl_R", 6.309573442966208, "FDM"),
    ]

    return design_name, description, corpus_type, study_params


def create_falcon_s8_rotated():
    design_name, description, corpus_type, study_params = falcon_s_platform(
        "8RotatedCargoCase",
        n_quads=2,
        cargo_rotation=135.5,
        forward_tube_length=95,
        wing_span=360,
        wing_chord=65,
        wing_gap=80,
        include_fdm=False
    )

    # Model-specific tweaks
    study_params = [
        *study_params,
        StudyParam("Flight_Path", 9, "FDM"),
        StudyParam("Requested_Lateral_Speed", [38, 35], "FDM"),
        StudyParam("Requested_Vertical_Speed", -13, "FDM"),
        StudyParam("Requested_Vertical_Down_Speed", [21, 18.5], "FDM"),
        StudyParam("Requested_Lateral_Acceleration", 3.5, "FDM"),
        StudyParam("Requested_Lateral_Deceleration", [-5.5, -6], "FDM"),
        StudyParam("Requested_Vertical_Acceleration", [-7.5, -8], "FDM"),
        StudyParam("Requested_Vertical_Deceleration", [17.5, 18], "FDM"),
        # James suggested not to tweak these
        # StudyParam("Landing_Approach_Height", 3, "FDM"),
        # StudyParam("Vertical_Landing_Speed", 0.5, "FDM"),    # not used in buildcad.py
        # StudyParam("Vertical_Landing_Speed_At_Ground", 0.1, "FDM"),
        StudyParam("Q_Position", 0.025118864315095798, "FDM"),
        StudyParam("Q_Velocity", 0.0015848931924611134, "FDM"),
        StudyParam("Q_Angular_Velocity", 15.848931924611142, "FDM"),
        StudyParam("Q_Angles", 0.6309573444801934, "FDM"),
        StudyParam("Ctrl_R", 10.0, "FDM"),
    ]

    return design_name, description, corpus_type, study_params


def falcon_s_platform(
    variant,
    n_quads=1,
    cargo_rotation=0.0,
    forward_tube_length=200,
    wing_span=390,
    wing_chord=55,
    wing_gap=50,
    include_fdm=True
):
    """
    Create a minimal design (does not include uam_direct2cad workflow at this time,
    it only creates the graph design).
    """
    corpus_type = "UAV"
    description = "Study Parameters for FalconS Platform direct2cad Run"
    design_name = "FalconS" + variant

    designer = Designer()
    designer.create_design(design_name)

    ########################################
    # Static params
    tube_od = 7.1374  # cannot be a study param (fixed CAD models)
    motor_type = "t_motor_AntigravityMN5008KV340"
    prop_type = "apc_propellers_13x14"
    battery_type = "Tattu25C23000mAh6S1PHV"

    ########################################
    # Tunable params
    wing_span = designer.set_study_param("wing_span", wing_span)
    # extra space (50mm) around the fuselage
    wing_tube_length = designer.set_study_param(
        "wing_tube_length", designer.param_value(wing_span) + wing_gap
    )
    wing_chord = designer.set_study_param("wing_chord", wing_chord)
    wing_load = designer.set_study_param("wing_load", 50)

    # distance of the motor plane from the wing root
    forward_tube_length = designer.set_study_param(
        "forward_tube_length", forward_tube_length
    )
    # horizontal separation between the motors
    motor_horiz_distance = designer.set_study_param(
        "motor_horiz_distance", 400
    )
    motor_horiz_center_distance = designer.set_study_param(
        "motor_horiz_center_distance",
        designer.param_value(motor_horiz_distance) // 2,
    )
    # vertical height of the top row of motors
    motor_vert_height = designer.set_study_param("motor_vert_height", 200)
    # vertical depth of the bottom row of motors
    motor_vert_depth = designer.set_study_param("motor_vert_depth", 200)
    cargo_mass = designer.set_study_param("CargoMass", [0.001, 0.5], "CargoMass")


    ########################################
    # Center (Hun, Fuselage, Cargo)
    fuselage = designer.add_fuselage_uav(
        name="fuselage",
        floor_height=14,
        fuse_width=112,
        fuse_height=125,
        fuse_cyl_length=368,
        # bottom_connector_rotation=0,
        bottom_connector_rotation=90,
    )

    # Setup cargo mass to represent a full cargo
    cargo_mass_list = designer.param_value(cargo_mass)
    cargo, cargo_case = designer.add_cargo(
        weight=cargo_mass_list[1], name="cargo", rotation=cargo_rotation  # type: ignore
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

    designer.add_battery_uav(
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

    wing_r = designer.add_wing_uav(
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

    wing_l = designer.add_wing_uav(
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

    designer.close_design(corpus="uav", orient_z_angle=90)


    if include_fdm:
        study_params = [
            StudyParam("Flight_Path", 9, "FDM"),
            StudyParam("Requested_Lateral_Speed", 32, "FDM"),
            StudyParam("Requested_Vertical_Speed", -8, "FDM"),
            StudyParam("Requested_Vertical_Down_Speed", 19, "FDM"),
            StudyParam("Requested_Lateral_Acceleration", 2, "FDM"),
            StudyParam("Requested_Lateral_Deceleration", -9, "FDM"),
            StudyParam("Requested_Vertical_Acceleration", -6, "FDM"),
            StudyParam("Requested_Vertical_Deceleration", 15, "FDM"),
            # James suggested not to tweak these
            # StudyParam("Landing_Approach_Height", 3, "FDM"),
            # StudyParam("Vertical_Landing_Speed", 0.5, "FDM"),    # not used in buildcad.py
            # StudyParam("Vertical_Landing_Speed_At_Ground", 0.1, "FDM"),
            StudyParam("Q_Position", 0.039810717, "FDM"),
            StudyParam("Q_Velocity", 0.001995262, "FDM"),
            StudyParam("Q_Angular_Velocity", 0.630957345, "FDM"),
            StudyParam("Q_Angles", 0.002511886, "FDM"),
            StudyParam("Ctrl_R", 1.584893192, "FDM"),
        ]
    else:
        study_params = []

    for val in locals().values():
        if isinstance(val, StudyParam):
            study_params.append(val)

    return design_name, description, corpus_type, study_params
