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


def create_tiltie():
    return tiltie_platform("", num_batts=2)


def create_tiltie_tailed():
    return tiltie_platform("Tailed", num_batts=1, narrow_fuse=True, tail=True)


def create_tiltie_trimmed():
    return tiltie_platform("Trimmed", num_batts=1, narrow_fuse=True, tail=False)


def create_tiltie_dyno():
    return tiltie_platform("Dyno", num_batts=1, narrow_fuse=False, tail=False)


def tiltie_platform(variant, num_batts=1, narrow_fuse=False, tail=False):
    """
    This design will place the cargo inline behind the fuselage, but under a single wing.
    The propellers will be tiltable and controllable by a system parameter.
    """
    assert num_batts in [1, 2]
    # Valid designs configured during hackathon 2
    if num_batts == 2:
        assert narrow_fuse == False and tail == False
    else:
        if narrow_fuse == False:
            assert tail == False

    design_name = "Tiltie" + variant
    designer = Designer()
    designer.create_design(design_name)

    ########################################
    # Static params
    tube_od = 7.1374
    motor_type = "t_motor_AntigravityMN5008KV340"
    prop_type = "apc_propellers_13x14"
    if num_batts == 2:
        battery_type = "TurnigyGraphene6000mAh6S75C"
    else:
        battery_type = "Tattu25C23000mAh6S1PHV"

    body_rot_angle = 180
    NACA_profile = "0012"
    wing_thickness = 12

    ########################################
    # Tunable params
    cargo_mass = designer.set_study_param("CargoMass", 0.5)

    if narrow_fuse:
        fuselage_floor_height = designer.set_study_param(
            "fuselage_floor_height", 14)
        fuselage_width = designer.set_study_param("fuselage_width", 112)
        fuselage_cyl_length = designer.set_study_param(
            "fuselage_cyl_length", 368)
    else:
        fuselage_floor_height = designer.set_study_param(
            "fuselage_floor_height", 20)
        fuselage_width = designer.set_study_param("fuselage_width", 190)
        if num_batts == 1:
            fuselage_cyl_length = designer.set_study_param(
                "fuselage_cyl_length", 289)
        else:
            fuselage_cyl_length = designer.set_study_param(
                "fuselage_cyl_length", 270)

    # Tube between main hub and center structure to move fuselage vertically
    fuse_vert_length = designer.set_study_param("fuse_vert_length", 20)

    cargo_tube_length = designer.set_study_param("cargo_tube_length", 305)
    cargo_attach_tube_length = designer.set_study_param(
        "cargo_attach_tube_length", 5)

    front_wing_span = designer.set_study_param("front_wing_span", 1200)
    front_wing_chord = designer.set_study_param("front_wing_chord", 150)
    front_wing_load = designer.set_study_param("front_wing_load", 30)
    front_wing_tube_offset = designer.param_value(front_wing_span) / 2
    front_wing_tube_length = designer.set_study_param(
        "front_wing_tube_length", 50)

    tail_extension_length = designer.set_study_param(
        "tail_extension_length", 200)
    tail_attach_tube_length = designer.set_study_param(
        "tail_attach_tube_length", 25)
    tail_tube_length = designer.set_study_param("tail_tube_length", 50)
    tail_wing_span = designer.set_study_param("tail_wing_span", 500)
    tail_wing_chord = designer.set_study_param("tail_wing_chord", 150)
    tail_wing_load = designer.set_study_param("tail_wing_load", 15)
    tail_tube_offset = designer.param_value(front_wing_span) / 2

    # Prop/Motor section
    prop_forward_length = designer.set_study_param("prop_forward_length", 250)
    top_vert_spread = designer.set_study_param("top_vert_spread", 50)
    bottom_vert_spread = designer.set_study_param("bottom_vert_spread", 100)
    prop_hort_spread_length = designer.set_study_param(
        "prop_hort_spread_length", 140)
    # From desired tilt_angle, on left: 360 - tilt_angle, on right: tilt_angle
    left_tilt_angle = designer.set_study_param("left_tilt_angle", 315)
    right_tilt_angle = designer.set_study_param("right_tilt_angle", 45)
    prop_tilt_tube_length = designer.set_study_param(
        "prop_tilt_tube_length", 50)

    ########################################
    # Center (Hub, Fuselage, Cargo)

    fuselage = designer.add_fuselage_uav(name="fuselage",
                                         floor_height=fuselage_floor_height,
                                         fuse_width=fuselage_width,
                                         fuse_height=125,
                                         fuse_cyl_length=fuselage_cyl_length,
                                         bottom_connector_rotation=0)
    cargo, cargo_case = designer.add_cargo(weight=cargo_mass,
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
    # Add batteries
    battery_control = designer.add_battery_controller(name="BatteryController")
    if num_batts == 2:
        designer.add_battery_uav(model=battery_type,
                                 name="Battery_1",
                                 fuse_conn_num=1,
                                 mount_length=0,
                                 mount_width=30,
                                 controller_inst=battery_control)

        designer.add_battery_uav(model=battery_type,
                                 name="Battery_2",
                                 fuse_conn_num=2,
                                 mount_length=0,
                                 mount_width=-30,
                                 controller_inst=battery_control)
    elif num_batts == 1:
        designer.add_battery_uav(model=battery_type,
                                 name="Battery_1",
                                 fuse_conn_num=1,
                                 mount_length=0,
                                 mount_width=0,
                                 controller_inst=battery_control)

    ########################################
    # Sensors
    if num_batts == 2:
        rpm_rotation = 90
        rpm_mount_length = -160
        rpm_mount_width = 13
        current_rotation = 90
        current_mount_length = -160
        current_mount_width = -18
        autopilot_rotation = 90
        autopilot_mount_length = 115
        autopilot_mount_width = 0
        voltage_rotation = 90
        voltage_mount_length = 155
        voltage_mount_width = 18
        gps_rotation = 0
        gps_mount_length = -120
        gps_mount_width = 0
        variometer_rotation = 90
        variometer_mount_length = 155
        variometer_mount_width = -18
    elif narrow_fuse and num_batts == 1:
        rpm_rotation = 90
        rpm_mount_length = -180
        rpm_mount_width = 16
        current_rotation = 90
        current_mount_length = -180
        current_mount_width = -15
        autopilot_rotation = 0
        autopilot_mount_length = 147
        autopilot_mount_width = 0
        voltage_rotation = 90
        voltage_mount_length = -202
        voltage_mount_width = 0
        gps_rotation = 0
        gps_mount_length = -140
        gps_mount_width = 0
        variometer_rotation = 90
        variometer_mount_length = 199
        variometer_mount_width = 0
    elif num_batts == 1:
        rpm_rotation = 90
        rpm_mount_length = -172
        rpm_mount_width = 13
        current_rotation = 90
        current_mount_length = -172
        current_mount_width = -18
        autopilot_rotation = 90
        autopilot_mount_length = 125
        autopilot_mount_width = 0
        voltage_rotation = 90
        voltage_mount_length = 162
        voltage_mount_width = 18
        gps_rotation = 0
        gps_mount_length = -130
        gps_mount_width = 0
        variometer_rotation = 90
        variometer_mount_length = 162
        variometer_mount_width = -18

    designer.add_sensor(sensor_model="RpmTemp",
                        name="RpmTemp",
                        mount_conn_num=3,
                        rotation=rpm_rotation,
                        mount_length=rpm_mount_length,
                        mount_width=rpm_mount_width)
    designer.add_sensor(sensor_model="Current",
                        name="Current",
                        mount_conn_num=4,
                        rotation=current_rotation,
                        mount_length=current_mount_length,
                        mount_width=current_mount_width)
    designer.add_sensor(sensor_model="Autopilot",
                        name="Autopilot",
                        mount_conn_num=5,
                        rotation=autopilot_rotation,
                        mount_length=autopilot_mount_length,
                        mount_width=autopilot_mount_width)
    designer.add_sensor(sensor_model="Voltage",
                        name="Voltage",
                        mount_conn_num=6,
                        rotation=voltage_rotation,
                        mount_length=voltage_mount_length,
                        mount_width=voltage_mount_width)
    designer.add_sensor(sensor_model="GPS",
                        name="GPS",
                        mount_conn_num=7,
                        rotation=gps_rotation,
                        mount_length=gps_mount_length,
                        mount_width=gps_mount_width)
    designer.add_sensor(sensor_model="Variometer",
                        name="Variometer",
                        mount_conn_num=8,
                        rotation=variometer_rotation,
                        mount_length=variometer_mount_length,
                        mount_width=variometer_mount_width)

    ########################################
    # Central Hub
    # Tube between main hub and center structure to move fuselage vertically
    fuse_hub_tube = designer.add_tube(od=tube_od,
                                      length=fuse_vert_length,
                                      end_rotation=0,
                                      name="fuse_hub_tube",
                                      mount_base_inst=hub_main,
                                      mount_base_conn="Top_Connector")
    center_hub = designer.add_hub(name="center_hub",
                                  num_connects=2,
                                  diameter=tube_od,
                                  connector_horizonal_angle=180,
                                  connector_vertical_angle=180,
                                  connects=["Bottom_Connector"],
                                  mount_inst=[fuse_hub_tube],
                                  mount_conn=["EndConnection"],
                                  orient_base=True)

    ########################################
    # Cargo section
    # - tube from 4 way hub (1) to 2 way hub
    center_cargo_tube = designer.add_tube(od=tube_od,
                                          length=cargo_tube_length,
                                          end_rotation=180,
                                          name="center_cargo_tube",
                                          mount_base_inst=center_hub,
                                          mount_base_conn="Side_Connector_2")
    if tail:
        back_hub = designer.add_hub(name="back_hub",
                                    num_connects=2,
                                    diameter=tube_od,
                                    connector_horizonal_angle=180,
                                    connects=["Side_Connector_1"],
                                    mount_inst=[center_cargo_tube],
                                    mount_conn=["EndConnection"])
    else:
        back_hub = designer.add_hub(name="back_hub",
                                    num_connects=2,
                                    diameter=tube_od,
                                    connector_horizonal_angle=0,
                                    connects=["Side_Connector_1"],
                                    mount_inst=[center_cargo_tube],
                                    mount_conn=["EndConnection"])
    cargo_attach_tube = designer.add_tube(od=tube_od,
                                          length=cargo_attach_tube_length,
                                          end_rotation=180,
                                          name="cargo_attach_tube",
                                          mount_base_inst=back_hub,
                                          mount_base_conn="Bottom_Connector")
    cargo_hub = designer.add_hub(name="cargo_hub",
                                 num_connects=2,
                                 diameter=tube_od,
                                 connector_horizonal_angle=0,
                                 connector_vertical_angle=0,
                                 connects=["Top_Connector",
                                           "Bottom_Connector"],
                                 mount_inst=[cargo_attach_tube, cargo_case],
                                 mount_conn=["EndConnection", "Case2HubConnector"])

    ########################################
    # Front Wing section
    #   2 horizontal tubes from 4 way hub (2 & 4) to 2 way hubs
    #   2 vertical tubes to attach to vertical wings

    front_wing_tube = designer.add_tube(od=tube_od,
                                        length=front_wing_tube_length,
                                        end_rotation=180,
                                        name="front_wing_tube",
                                        mount_base_inst=center_hub,
                                        mount_base_conn="Top_Connector")
    front_wing = designer.add_wing_uav(direction="Vertical",
                                       chord=front_wing_chord,
                                       span=front_wing_span,
                                       thickness=wing_thickness,
                                       load=front_wing_load,
                                       naca=NACA_profile,
                                       tube_diameter=tube_od,
                                       tube_offset=front_wing_tube_offset,
                                       tube_rotation=180,
                                       channel=1,
                                       name="front_wing",
                                       tube_inst=front_wing_tube,
                                       tube_conn="EndConnection")

    ########################################
    # Optional V-Tail
    if tail:
        tail_extension_tube = designer.add_tube(od=tube_od,
                                                length=tail_extension_length,
                                                end_rotation=0,
                                                name="tail_extension_tube",
                                                mount_base_inst=back_hub,
                                                mount_base_conn="Side_Connector_2")
        tail_hub = designer.add_hub(name="tail_hub",
                                    num_connects=2,
                                    diameter=tube_od,
                                    connector_horizonal_angle=0,
                                    connects=["Side_Connector_1"],
                                    mount_inst=[tail_extension_tube],
                                    mount_conn=["EndConnection"])
        tail_attach_tube = designer.add_tube(od=tube_od,
                                             length=tail_attach_tube_length,
                                             end_rotation=180,
                                             name="tail_attach_tube",
                                             mount_base_inst=tail_hub,
                                             mount_base_conn="Top_Connector")
        tail_wing_hub = designer.add_hub(name="tail_wing_hub",
                                         num_connects=3,
                                         diameter=tube_od,
                                         connector_horizonal_angle=120,
                                         connector_vertical_angle=0,
                                         connects=["Side_Connector_1"],
                                         mount_inst=[tail_attach_tube],
                                         mount_conn=["EndConnection"])
        tail_tube_l = designer.add_tube(od=tube_od,
                                        length=tail_tube_length,
                                        end_rotation=180,
                                        name="tail_tube_l",
                                        mount_base_inst=tail_wing_hub,
                                        mount_base_conn="Side_Connector_3")
        tail_tube_r = designer.add_tube(od=tube_od,
                                        length=tail_tube_length,
                                        end_rotation=180,
                                        name="tail_tube_r",
                                        mount_base_inst=tail_wing_hub,
                                        mount_base_conn="Side_Connector_2")
        tail_wing_l = designer.add_wing_uav(direction="Horizontal",
                                            chord=tail_wing_chord,
                                            span=tail_wing_span,
                                            thickness=wing_thickness,
                                            load=tail_wing_load,
                                            naca=NACA_profile,
                                            tube_diameter=tube_od,
                                            tube_offset=tail_tube_offset,
                                            tube_rotation=0,
                                            channel=1,
                                            name="tail_wing_l",
                                            tube_inst=tail_tube_l,
                                            tube_conn="EndConnection")
        tail_wing_r = designer.add_wing_uav(direction="Horizontal",
                                            chord=tail_wing_chord,
                                            span=tail_wing_span,
                                            thickness=wing_thickness,
                                            load=tail_wing_load,
                                            naca=NACA_profile,
                                            tube_diameter=tube_od,
                                            tube_offset=tail_tube_offset,
                                            tube_rotation=0,
                                            channel=1,
                                            name="tail_wing_r",
                                            tube_inst=tail_tube_r,
                                            tube_conn="EndConnection")

    ########################################
    # Prop/motor section
    #   tube from 4 way hub (3) to 3 way hub
    #   2 tubes horizontally to 3 way hubs
    #   2 vertical tubes out from 3 hubs (on each side) to flanges
    #   4 prop/motors attached to flanges
    center_tube_prop = designer.add_tube(od=tube_od,
                                         length=prop_forward_length,
                                         end_rotation=0,
                                         name="center_tube_prop",
                                         mount_base_inst=center_hub,
                                         mount_base_conn="Side_Connector_1")
    front_hub = designer.add_hub(name="front_hub",
                                 num_connects=3,
                                 diameter=tube_od,
                                 connector_horizonal_angle=180,
                                 connects=["Center_Connector"],
                                 mount_inst=[center_tube_prop],
                                 mount_conn=["EndConnection"])
    top_vert_prop_tube = designer.add_tube(od=tube_od,
                                           length=top_vert_spread,
                                           end_rotation=90,
                                           name="top_vert_prop_tube",
                                           mount_base_inst=front_hub,
                                           mount_base_conn="Side_Connector_1")
    bottom_vert_prop_tube = designer.add_tube(od=tube_od,
                                              length=bottom_vert_spread,
                                              end_rotation=90,
                                              name="bottom_vert_prop_tube",
                                              mount_base_inst=front_hub,
                                              mount_base_conn="Side_Connector_2")
    top_prop_hub = designer.add_hub(name="top_prop_hub",
                                    num_connects=2,
                                    diameter=tube_od,
                                    connector_horizonal_angle=180,
                                    connects=["Bottom_Connector"],
                                    mount_inst=[top_vert_prop_tube],
                                    mount_conn=["EndConnection"])
    bottom_prop_hub = designer.add_hub(name="bottom_prop_hub",
                                       num_connects=2,
                                       diameter=tube_od,
                                       connector_horizonal_angle=180,
                                       connects=["Top_Connector"],
                                       mount_inst=[bottom_vert_prop_tube],
                                       mount_conn=["EndConnection"])
    top_prop_hort_tube_l = designer.add_tube(od=tube_od,
                                             length=prop_hort_spread_length,
                                             end_rotation=left_tilt_angle,
                                             name="top_prop_hort_tube_l",
                                             mount_base_inst=top_prop_hub,
                                             mount_base_conn="Side_Connector_1")
    top_prop_hort_tube_r = designer.add_tube(od=tube_od,
                                             length=prop_hort_spread_length,
                                             end_rotation=right_tilt_angle,
                                             name="top_prop_hort_tube_r",
                                             mount_base_inst=top_prop_hub,
                                             mount_base_conn="Side_Connector_2")
    bottom_prop_hort_tube_l = designer.add_tube(od=tube_od,
                                                length=prop_hort_spread_length,
                                                end_rotation=left_tilt_angle,
                                                name="bottom_prop_hort_tube_l",
                                                mount_base_inst=bottom_prop_hub,
                                                mount_base_conn="Side_Connector_2")
    bottom_prop_hort_tube_r = designer.add_tube(od=tube_od,
                                                length=prop_hort_spread_length,
                                                end_rotation=right_tilt_angle,
                                                name="bottom_prop_hort_tube_r",
                                                mount_base_inst=bottom_prop_hub,
                                                mount_base_conn="Side_Connector_1")
    top_prop_hub_l = designer.add_hub(name="top_prop_hub_l",
                                      num_connects=2,
                                      diameter=tube_od,
                                      connector_horizonal_angle=90,
                                      connector_vertical_angle=0,
                                      connects=["Side_Connector_1"],
                                      mount_inst=[top_prop_hort_tube_l],
                                      mount_conn=["EndConnection"])
    top_prop_hub_r = designer.add_hub(name="top_prop_hub_r",
                                      num_connects=2,
                                      diameter=tube_od,
                                      connector_horizonal_angle=90,
                                      connector_vertical_angle=0,
                                      connects=["Side_Connector_2"],
                                      mount_inst=[top_prop_hort_tube_r],
                                      mount_conn=["EndConnection"])
    bottom_prop_hub_l = designer.add_hub(name="bottom_prop_hub_l",
                                         num_connects=2,
                                         diameter=tube_od,
                                         connector_horizonal_angle=90,
                                         connector_vertical_angle=0,
                                         connects=["Side_Connector_2"],
                                         mount_inst=[bottom_prop_hort_tube_l],
                                         mount_conn=["EndConnection"])
    bottom_prop_hub_r = designer.add_hub(name="bottom_prop_hub_r",
                                         num_connects=2,
                                         diameter=tube_od,
                                         connector_horizonal_angle=90,
                                         connector_vertical_angle=0,
                                         connects=["Side_Connector_1"],
                                         mount_inst=[bottom_prop_hort_tube_r],
                                         mount_conn=["EndConnection"])
    top_prop_tilt_tube_l = designer.add_tube(od=tube_od,
                                             length=prop_tilt_tube_length,
                                             end_rotation=0,
                                             name="top_prop_tilt_tube_l",
                                             mount_base_inst=top_prop_hub_l,
                                             mount_base_conn="Side_Connector_2")
    top_prop_tilt_tube_r = designer.add_tube(od=tube_od,
                                             length=prop_tilt_tube_length,
                                             end_rotation=0,
                                             name="top_prop_tilt_tube_r",
                                             mount_base_inst=top_prop_hub_r,
                                             mount_base_conn="Side_Connector_1")
    top_prop_flange_l = designer.add_flange(hole_diameter=tube_od,
                                            name="top_prop_flange_l",
                                            mount_side_inst=top_prop_tilt_tube_l,
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
                                            mount_side_inst=top_prop_tilt_tube_r,
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
    bottom_prop_tilt_tube_l = designer.add_tube(od=tube_od,
                                                length=prop_tilt_tube_length,
                                                end_rotation=0,
                                                name="bottom_prop_tilt_tube_l",
                                                mount_base_inst=bottom_prop_hub_l,
                                                mount_base_conn="Side_Connector_1")
    bottom_prop_tilt_tube_r = designer.add_tube(od=tube_od,
                                                length=prop_tilt_tube_length,
                                                end_rotation=0,
                                                name="bottom_prop_tilt_tube_r",
                                                mount_base_inst=bottom_prop_hub_r,
                                                mount_base_conn="Side_Connector_2")
    bottom_prop_flange_l = designer.add_flange(hole_diameter=tube_od,
                                               name="bottom_prop_flange_l",
                                               mount_side_inst=bottom_prop_tilt_tube_l,
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
                                               mount_side_inst=bottom_prop_tilt_tube_r,
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
