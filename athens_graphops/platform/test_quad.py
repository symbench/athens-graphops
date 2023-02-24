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

# This is the TestQuad_Cargo seed design


def create_test_quad():
    return quad_platform("Test")

# Uses largest battery


def create_super_quad():
    return quad_platform("Super", large_battery=True)


def quad_platform(variant, large_battery=False):
    """
    Four motor/propeller sets around a fuselage and cargo 
    """
    corpus_type = "UAV"
    description = "Study Parameters for Quad Platform direct2cad Run"
    design_name = variant + "QuadVU"


    designer = Designer()
    designer.create_design(design_name)

    ########################################
    # Static params
    if large_battery:
        battery_type = "TattuPlus25C22000mAh12S1PAGRI"
        motor_type = "kde_direct_KDE700XF_455_G3"
        propeller_type = "apc_propellers_20x10"
        # Battery and Sensor placement
        offset1_length = 120
        offset1_width = 0
        offset2_length = -120
        offset2_width = 0
        offset3_length = 292
        offset3_width = 0
        offset4_length = -265
        offset4_width = -45
        offset5_length = 260
        offset5_width = 5
        offset6_length = -264
        offset6_width = 44
        offset7_length = -274
        offset7_width = 0
        offset8_length = 260
        offset8_width = -50
    else:
        battery_type = "TurnigyGraphene6000mAh6S75C"
        motor_type = "t_motor_AT4130KV300"
        propeller_type = "apc_propellers_17x6"
        # Battery and Sensor placement
        offset1_length = 0
        offset1_width = 30
        offset2_length = 0
        offset2_width = -30
        offset3_length = -160
        offset3_width = 13
        offset4_length = -160
        offset4_width = -18
        offset5_length = 115
        offset5_width = 0
        offset6_length = 155
        offset6_width = 18
        offset7_length = -120
        offset7_width = 0
        offset8_length = 155
        offset8_width = -18

    tube_od = 7.1374
    angle_1 = 45
    angle_2 = 90

    ########################################
    # Tunable params
    cargo_mass = designer.set_study_param("CargoMass", [0.001, 0.5], "CargoMass")
    fuse_floor = designer.set_study_param("fuse_floor", 20)
    if large_battery:
        fuse_width = designer.set_study_param("fuse_width", 250)
        fuse_height = designer.set_study_param("fuse_height", 220)
        fuse_length = designer.set_study_param("fuse_length", 505)
        arm_length = designer.set_study_param("arm_length", 520)
    else:
        fuse_width = designer.set_study_param("fuse_width", 190)
        fuse_height = designer.set_study_param("fuse_height", 125)
        fuse_length = designer.set_study_param("fuse_length", 270)
        arm_length = designer.set_study_param("arm_length", 400)

    leg_length = designer.set_study_param("leg_length", 170)

    ########################################
    # Center (Hub, Fuselage, Cargo)
    fuselage = designer.add_fuselage_uav(name="fuselage",
                                         floor_height=fuse_floor,
                                         fuse_width=fuse_width,
                                         fuse_height=fuse_height,
                                         fuse_cyl_length=fuse_length,
                                         bottom_connector_rotation=angle_1)
    # Setup cargo mass to represent a full cargo
    cargo_mass_list = designer.param_value(cargo_mass)
    cargo, cargo_case = designer.add_cargo(weight=cargo_mass_list[1],
                                           name="cargo")

    # Require main_hub for connection to Orient
    # Create hub connection lists (size of num_connections max)
    # Not all connections are needed
    hub_main = designer.add_hub(name="main_hub",
                                num_connects=4,
                                connector_horizonal_angle=90,
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
                             fuse_conn_num=1,
                             mount_length=offset1_length,
                             mount_width=offset1_width,
                             controller_inst=battery_control)

    designer.add_battery_uav(model=battery_type,
                             name="Battery_2",
                             fuse_conn_num=2,
                             mount_length=offset2_length,
                             mount_width=offset2_width,
                             controller_inst=battery_control)

    ########################################
    # Sensors
    designer.add_sensor(sensor_model="RpmTemp",
                        name="RpmTemp",
                        mount_conn_num=3,
                        rotation=angle_2,
                        mount_length=offset3_length,
                        mount_width=offset3_width)
    designer.add_sensor(sensor_model="Current",
                        name="Current",
                        mount_conn_num=4,
                        rotation=angle_2,
                        mount_length=offset4_length,
                        mount_width=offset4_width)
    designer.add_sensor(sensor_model="Autopilot",
                        name="Autopilot",
                        mount_conn_num=5,
                        rotation=angle_2,
                        mount_length=offset5_length,
                        mount_width=offset5_width)
    designer.add_sensor(sensor_model="Voltage",
                        name="Voltage",
                        mount_conn_num=6,
                        rotation=angle_2,
                        mount_length=offset6_length,
                        mount_width=offset6_width)
    designer.add_sensor(sensor_model="GPS",
                        name="GPS",
                        mount_conn_num=7,
                        mount_length=offset7_length,
                        mount_width=offset7_width)
    designer.add_sensor(sensor_model="Variometer",
                        name="Variometer",
                        mount_conn_num=8,
                        rotation=angle_2,
                        mount_length=offset8_length,
                        mount_width=offset8_width)

    ########################################
    # Propeller/Motor Sets
    # Add 4 propeller/motors
    for x in range(4):
        # print("X={}".format(str(x)))
        arm_name = "arm_" + str(x + 1)
        hub_conn_name = "Side_Connector_" + str(x + 1)
        flange_name = "flange_" + str(x + 1)
        leg_name = "leg_" + str(x + 1)
        prefix = "mp_" + str(x + 1)
        channel = x + 1

        if x == 0:
            direction = -1
            spin = -1
        elif x == 1:
            direction = 1
            spin = 1
        elif x == 2:
            if large_battery:
                direction = 1
                spin = 1
            else:
                direction = -1
                spin = -1
        elif x == 3:
            if large_battery:
                direction = -1
                spin = -1
            else:
                direction = 1
                spin = 1

        arm_inst = designer.add_tube(od=tube_od,
                                     length=arm_length,
                                     name=arm_name,
                                     mount_base_inst=hub_main,
                                     mount_base_conn=hub_conn_name)
        flange_inst = designer.add_flange(hole_diameter=tube_od,
                                          name=flange_name,
                                          mount_side_inst=arm_inst,
                                          mount_side_conn="EndConnection")
        designer.add_tube(od=tube_od,
                          length=leg_length,
                          name=leg_name,
                          mount_base_inst=flange_inst,
                          mount_base_conn="BottomConnector")
        designer.add_motor_propeller(motor_model=motor_type,
                                     prop_model=propeller_type,
                                     prop_type=spin,
                                     direction=direction,
                                     control_channel=channel,
                                     name_prefix=prefix,
                                     mount_inst=flange_inst,
                                     mount_conn="TopConnector",
                                     controller_inst=battery_control)

    designer.close_design(corpus="uav", orient_z_angle=angle_1)

    """
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
        StudyParam("Q_Position", 0.158489319, "FDM"),
        StudyParam("Q_Velocity", 0.0158489319, "FDM"),
        StudyParam("Q_Angular_Velocity", 0.501187234, "FDM"),
        StudyParam("Q_Angles", 0.01, "FDM"),
        StudyParam("Ctrl_R", 0.316227766, "FDM")
    ]
    """

    study_params = [
        StudyParam("Flight_Path", [8, 9], "FDM"),
        StudyParam("Requested_Lateral_Speed", [23, 22], "FDM"),
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
        StudyParam("Q_Position", 0.158489319, "FDM"),
        StudyParam("Q_Velocity", 0.0158489319, "FDM"),
        StudyParam("Q_Angular_Velocity", 0.501187234, "FDM"),
        StudyParam("Q_Angles", 0.01, "FDM"),
        StudyParam("Ctrl_R", 0.316227766, "FDM")
    ]

    # Add all study parameters automatically
    for val in locals().values():
        if isinstance(val, StudyParam):
            study_params.append(val)

    """
    study_params_dict = {}
    for param in study_params:
        study_params_dict[param.name] = param.value

    for val in locals().values():
        if isinstance(val, StudyParam):
            study_params_dict[val.name] = val.value

    return design_name, study_params_dict
    """
    return design_name, description, corpus_type, study_params
