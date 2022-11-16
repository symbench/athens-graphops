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


def create_tie4():
    return tie_platform("4", n_motors=4)


# NOTE: only add platform-specific parameters with structural effects
def tie_platform(variant, n_motors=4):
    design_name = "TIE" + variant

    designer = Designer()
    designer.create_design(design_name)

    ########################################
    # Static params
    tube_od = 7.1374  # cannot be a study param (fixed CAD models)
    motor_type = "t_motor_AntigravityMN4006KV380"
    prop_type = "apc_propellers_12x3_8SF"

    ########################################
    # Tunable params
    wing_vert_span = designer.set_study_param("wing_vert_span", 300)
    wing_vert_halfspan = designer.set_study_param(
        "wing_vert_halfspan", designer.param_value(wing_vert_span) / 2
    )
    wing_slant_span = designer.set_study_param("wing_slant_span", 400)
    wing_slant_halfspan = designer.set_study_param(
        "wing_slant_halfspan", designer.param_value(wing_slant_span) / 2
    )
    wing_slant_angle = designer.set_study_param("wing_slant_angle", 135)
    wing_side_distance = designer.set_study_param("wing_vert_distance", 500)
    wing_chord = designer.set_study_param("wing_chord", 100)
    wing_load = designer.set_study_param("wing_load", 25)

    forward_tube_length = designer.set_study_param("forward_tube_length", 200)
    motor_spoke_length = designer.set_study_param("motor_spoke_length", 220)
    motor_rotation = designer.set_study_param(
        "motor_rotation",
        180 // n_motors
        # "motor_rotation", 0
    )

    cargo_mass = designer.set_study_param("CargoMass", 0.5)

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
    wing_channel = n_motors + 1
    for side, anchor in (
        ("r", (main_hub, "Side_Connector_1")),
        ("l", (main_hub, "Side_Connector_3")),
    ):
        side_tube = designer.add_tube(
            name=f"side_tube_{side}",
            od=tube_od,
            length=wing_side_distance,
            offset_1=60,
            base_rotation=90 if side == "r" else 270,
            mount_end_inst=anchor[0],
            mount_end_conn=anchor[1],
        )

        side_hub = designer.add_hub(
            name=f"side_hub_{side}",
            diameter=tube_od,
            num_connects=2,
            connector_horizonal_angle=180,
            connects=["Bottom_Connector"],
            mount_inst=[side_tube],
            mount_conn=["OffsetConnection1"],
        )

        wing = designer.add_wing(
            name=f"wing_vert_{side}",
            direction="Vertical",
            chord=wing_chord,
            span=wing_vert_span,
            thickness=12,
            naca="0012",
            load=wing_load,  # type: ignore
            tube_diameter=tube_od,
            tube_offset=wing_vert_halfspan,  # type: ignore
            # channel=wing_channel,
            channel=0,
            tube_inst=side_tube,
            tube_conn="BaseConnection",
        )
        # wing_channel += 1

        for floor, anchor in (
            ("top", (side_hub, "Side_Connector_1")),
            ("bottom", (side_hub, "Side_Connector_2")),
        ):
            vert_tube = designer.add_tube(
                name=f"side_tube_{side}_{floor}",
                od=tube_od,
                length=wing_vert_halfspan,
                base_rotation=270,
                mount_base_inst=anchor[0],
                mount_base_conn=anchor[1],
            )

            slant_hub = designer.add_hub(
                name=f"slant_hub_{side}_{floor}",
                diameter=tube_od,
                num_connects=2,
                connector_horizonal_angle=wing_slant_angle,  # type: ignore
                connects=["Side_Connector_1"],
                mount_inst=[vert_tube],
                mount_conn=["EndConnection"],
            )

            slant_tube = designer.add_tube(
                name=f"slant_tube_{side}_{floor}",
                od=tube_od,
                length=wing_slant_halfspan,
                base_rotation=180,
                mount_base_inst=slant_hub,
                mount_base_conn="Side_Connector_2",
            )

            end_hub = designer.add_hub(
                name=f"end_hub_{side}_{floor}",
                diameter=tube_od,
                num_connects=2,
                connector_horizonal_angle=90,
                connects=["Side_Connector_1"],
                mount_inst=[slant_tube],
                mount_conn=["EndConnection"],
            )

            end_tube = designer.add_tube(
                name=f"end_tube_{side}_{floor}",
                od=tube_od,
                length=50,
                base_rotation=180
                if (
                    (side == "r" and floor == "top")
                    or (side == "l" and floor == "bottom")
                )
                else 0,
                mount_base_inst=end_hub,
                mount_base_conn="Side_Connector_2",
            )

            wing = designer.add_wing(
                name=f"wing_slant_{side}_{floor}",
                direction="Vertical",
                chord=wing_chord,
                span=wing_slant_span,
                thickness=12,
                naca="0012",
                load=wing_load,  # type: ignore
                tube_diameter=tube_od,
                tube_offset=wing_slant_halfspan,  # type: ignore
                channel=wing_channel,
                tube_inst=end_tube,
                tube_conn="EndConnection",
            )
            wing_channel += 1

    ########################################
    # Forward structure with motors
    forward_tube = designer.add_tube(
        name="forward_tube",
        od=tube_od,
        length=forward_tube_length,
        end_rotation=motor_rotation,  # type: ignore
        mount_base_inst=main_hub,
        mount_base_conn="Side_Connector_4",
    )

    forward_hub = designer.add_hub(
        name="forward_hub",
        diameter=tube_od,
        num_connects=n_motors,
        connector_horizonal_angle=360 // n_motors,
        connects=["Bottom_Connector"],
        mount_inst=[forward_tube],
        mount_conn=["EndConnection"],
    )

    for i_motor in range(1, n_motors + 1):
        motor_spoke = designer.add_tube(
            name=f"motor_spoke{i_motor}",
            od=tube_od,
            length=motor_spoke_length,
            mount_base_inst=forward_hub,
            mount_base_conn=f"Side_Connector_{i_motor}",
        )

        motor_flange = designer.add_flange(
            name=f"motor_flange{i_motor}",
            hole_diameter=tube_od,
            mount_side_inst=motor_spoke,
            mount_side_conn="EndConnection",
        )

        designer.add_motor_propeller(
            name_prefix=f"motor{i_motor}",
            motor_model=motor_type,
            prop_model=prop_type,
            prop_type=(-1) ** i_motor,
            direction=(-1) ** i_motor,
            control_channel=i_motor,
            mount_inst=motor_flange,
            mount_conn="TopConnector",
            controller_inst=battery_control,
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
        "Q_Position": 3.981071705534973,
        "Q_Velocity": 0.07924465962305567,
        "Q_Angular_Velocity": 100.0,
        "Q_Angles": 0.03154786722400965,
        "Ctrl_R": 2.5,
    }

    # Add all study parameters automatically
    for val in locals().values():
        if isinstance(val, StudyParam):
            study_params[val.name] = val.value

    study_params = sweep_study_param(
        study_params, cargo_mass.name, [0.5, 0.001]
    )

    return design_name, study_params
