#!/usr/bin/env python3
# Copyright (C) 2022, Miklos Maroti
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

# This is Peter's sandbox for Hackathon 2
import math

from .query import Client
from .dataset import get_model_data


class Instance:
    def __init__(self, model, name):
        self.model = model
        self.name = name
        self.parameters = dict()


class StudyParam:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class Designer:
    def __init__(self):
        self.client = None

    def create_design(self, design):
        assert self.client is None
        self.client = Client()
        self.instances = dict()
        self.nextid = 1

        self.design = design
        print("Creating design", self.design)
        self.client.create_design(self.design)

        self.fuselage = None

    def generate_name(self):
        instance = "inst_{:04}".format(self.nextid)
        self.nextid += 1
        return instance

    def add_instance(self, model, name):
        assert self.client and self.design
        assert name is None or isinstance(name, str)
        if not name:
            name = self.generate_name()

        assert name not in self.instances

        data = get_model_data(model)
        assert data

        instance = Instance(model, name)
        self.instances[name] = instance

        print("Creating", model, name)
        self.client.create_instance(self.design, model, name)

        return instance

    def connect(
        self,
        instance1,
        connector1,
        instance2,
        connector2,
    ):
        assert self.client and self.design
        assert isinstance(instance1, Instance) and isinstance(
            instance2, Instance
        )

        print(
            "Creating connection from",
            instance1.name,
            connector1,
            "to",
            instance2.name,
            connector2,
        )
        self.client.create_connection(
            self.design, instance1.name, connector1, instance2.name, connector2
        )

    def set_param(self, instance, param, value):
        assert self.client and self.design
        assert isinstance(instance, Instance)

        if not isinstance(value, StudyParam):
            param_name = instance.name + "_" + param
            self.client.create_parameter(self.design, param_name, value)
        else:
            param_name = value.name

        self.client.assign_parameter(
            self.design, instance.name, param, param_name
        )

    def set_study_param(self, param, value):
        assert self.client and self.design
        self.client.create_parameter(self.design, param, value)
        return StudyParam(param, value)

    @classmethod
    def param_value(cls, param):
        if isinstance(param, StudyParam):
            return param.value
        return param

    # capsule_fuselage class
    def add_fuselage(
        self,
        floor_height,
        fuse_width,
        fuse_height,
        fuse_cyl_length,
        bottom_connector_offset_length=0,
        bottom_connector_offset_width=0,
        bottom_connector_rotation=0,
        name=None,
    ):
        assert self.fuselage is None
        # provided by SwRI
        assert self.param_value(floor_height) > 0
        assert self.param_value(floor_height) < self.param_value(fuse_height)

        instance = self.add_instance("capsule_fuselage", name)
        self.set_param(instance, "FLOOR_HEIGHT", floor_height)
        self.set_param(instance, "HORZ_DIAMETER", fuse_width)
        self.set_param(instance, "VERT_DIAMETER", fuse_height)
        self.set_param(instance, "FUSE_CYL_LENGTH", fuse_cyl_length)
        self.set_param(
            instance,
            "BOTTOM_CONNECTOR_OFFSET_LENGTH",
            bottom_connector_offset_length,
        )
        self.set_param(
            instance,
            "BOTTOM_CONNECTOR_OFFSET_WIDTH",
            bottom_connector_offset_width,
        )
        self.set_param(
            instance, "BOTTOM_CONNECTOR_ROTATION", bottom_connector_rotation
        )

        self.fuselage = instance
        return instance

    # Add cargo and cargo case
    def add_cargo(
        self,
        weight=0.5,
        rotation=0,
        name=None,
        mount_inst=None,
        mount_conn=None,
    ):

        # Only two weights are valid
        assert self.param_value(weight) in [0.5, 0.01]

        instance_cargo = self.add_instance("Cargo", name)
        self.set_param(instance_cargo, "WEIGHT", weight)

        # add cargo case (for attachment)
        case_name = instance_cargo.name + "_case"
        instance_case = self.add_instance("CargoCase", case_name)
        self.set_param(instance_case, "Rotation", rotation)

        # mount cargo in case
        self.connect(
            instance_case, "CargoConnector", instance_cargo, "CargoConnector"
        )

        # mount case to the fuselage
        if mount_inst:
            self.connect(
                instance_case, "Case2HubConnector", mount_inst, mount_conn
            )

        return instance_cargo, instance_case

    # Tubes (of the same size as flange) are inserted into the flange
    def add_flange(
        self,
        hole_diameter,
        bottom_angle=0,
        side_angle=0,
        name=None,
        mount_top_inst=None,
        mount_top_conn=None,
        mount_bottom_inst=None,
        mount_bottom_conn=None,
        mount_side_inst=None,
        mount_side_conn=None,
    ):

        # models to hole (tube OD) sizes
        flange_models = {
            "0281_para_flange": 7.1374,
            "0394_para_flange": 10.0076,
            "05OD_para_flange": 12.7,
        }

        if isinstance(hole_diameter, StudyParam):
            print(
                "WARNING: flange hole dia is a study parameter (fixed CAD part"
            )
            hole_diameter = self.param_value(hole_diameter)

        for flange_model, flange_hole_diameter in flange_models.items():
            if math.isclose(hole_diameter, flange_hole_diameter, rel_tol=1e-3):
                break
        else:
            raise ValueError("Invalid flange hole diameter", hole_diameter)

        instance = self.add_instance(flange_model, name)
        self.set_param(instance, "BOTTOM_ANGLE", bottom_angle)
        self.set_param(instance, "SIDE_ANGLE", side_angle)

        if mount_top_inst:
            self.connect(
                instance, "TopConnector", mount_top_inst, mount_top_conn
            )
        if mount_bottom_inst:
            self.connect(
                instance,
                "BottomConnector",
                mount_bottom_inst,
                mount_bottom_conn,
            )
        if mount_side_inst:
            self.connect(
                instance, "SideConnector", mount_side_inst, mount_side_conn
            )

        return instance

    def add_tube(
        self,
        od,
        length,
        base_rotation=0,
        end_rotation=0,
        offset_1=0,
        offset_2=0,
        name=None,
        mount_base_inst=None,
        mount_base_conn=None,
        mount_end_inst=None,
        mount_end_conn=None,
    ):
        # models to tube OD sizes
        tube_models = {
            "0281OD_para_tube": 7.1374,
            "0394OD_para_tube": 10.0076,
            "05OD_para_tube": 12.7,
        }

        if isinstance(od, StudyParam):
            print("WARNING: tube OD is a study parameter (fixed CAD part")
            od = self.param_value(od)

        for tube_model, tube_od in tube_models.items():
            if math.isclose(od, tube_od, rel_tol=1e-3):
                break
        else:
            raise ValueError("Invalid tube OD", od)

        instance = self.add_instance(tube_model, name)
        self.set_param(instance, "Length", length)

        # larger sizes do not have these parameters
        self.set_param(instance, "BASE_ROT", base_rotation)
        self.set_param(instance, "END_ROT", end_rotation)
        self.set_param(instance, "Offset1", offset_1)
        self.set_param(instance, "Offset2", offset_2)

        if mount_base_inst:
            self.connect(
                instance, "BaseConnection", mount_base_inst, mount_base_conn
            )
        if mount_end_inst:
            self.connect(
                instance, "EndConnection", mount_end_inst, mount_end_conn
            )

        return instance

    # 5 hub options
    # Connects, mount_inst and mount_conn are lists that indicates:
    #    connects: which hub connections to use
    #    mount_inst: the component instance mounting to the connects  (same size as connects list)
    #    mount_conn: the mount_inst connection  (same size as connects list)
    # orient_base is a bool to identify which hub is the main_hub that connects
    #    to Orient in the close_design function, true make it as the main_hub
    def add_hub(
        self,
        num_connects,
        diameter=10.0076,
        connector_horizonal_angle=120,
        connector_vertical_angle=0,
        name=None,
        connects=None,
        mount_inst=None,
        mount_conn=None,
        orient_base=False,
    ):

        assert(2 <= self.param_value(num_connects) <= 6)
        hub_model = "0394od_para_hub_" + str(num_connects)
        instance = self.add_instance(hub_model, name)
        self.set_param(instance, "DIAMETER", diameter)
        self.set_param(instance, "ANGHORZCONN", connector_horizonal_angle)
        self.set_param(instance, "ANGVERTCONN", connector_vertical_angle)

        if connects:
            assert mount_inst and len(connects) == len(mount_inst)
            assert mount_conn and len(connects) == len(mount_conn)

            for i in range(len(connects)):
                self.connect(
                    instance, connects[i], mount_inst[i], mount_conn[i]
                )

        # main_hub will be where the connection to Orient occurs
        if orient_base == True:
            self.main_hub = instance

        return instance

    # 6 sensor options
    # If indicating mount connection number, also indicate the mount_length and mount_width
    # to allow connector placement on the fuselage floor
    def add_sensor(
        self,
        sensor_model,
        rotation=0,
        name=None,
        mount_conn_num=None,
        mount_length=0,
        mount_width=0,
    ):

        assert self.fuselage is not None

        instance = self.add_instance(sensor_model, name)
        self.set_param(instance, "ROTATION", rotation)

        mount_conn_num = self.param_value(mount_conn_num)
        if mount_conn_num:
            connect_length_name = (
                "FLOOR_CONNECTOR_" + str(mount_conn_num) + "_DISP_LENGTH"
            )
            connect_width_name = (
                "FLOOR_CONNECTOR_" + str(mount_conn_num) + "_DISP_WIDTH"
            )
            connect_name = "FloorConnector" + str(mount_conn_num)
            self.set_param(self.fuselage, connect_length_name, mount_length)
            self.set_param(self.fuselage, connect_width_name, mount_width)
            self.connect(
                instance, "SensorConnector", self.fuselage, connect_name
            )

        return instance

    # Common components
    # -----------------
    def add_battery_controller(self, name=None):
        instance = self.add_instance("BatteryController", name)
        return instance

    def add_wing(
        self,
        direction,
        chord,
        span,
        thickness,
        naca,
        load=15,
        tube_diameter=10.0,
        tube_offset=100.0,
        tube_rotation=0,
        taper_offset=0,
        channel=0,
        flap_bias=0.5,
        aileron_bias=0.5,
        servo_length=0.1,
        servo_thickness=0.1,
        servo_width=0.1,
        name=None,
        tube_inst=None,
        tube_conn=None,
    ):
        assert len(self.param_value(naca)) == 4
        assert self.param_value(chord) >= 1
        assert self.param_value(span) >= 1
        assert self.param_value(load) >= 1
        direction = self.param_value(direction)
        assert direction in ["Horizontal", "Vertical"]
        thickness = int(self.param_value(naca[2:4]))

        if direction == "Horizontal":
            instance = self.add_instance("Wing_horiz_hole", name)
        else:
            instance = self.add_instance("Wing_vert_hole", name)

        self.set_param(instance, "CHORD_1", chord)
        self.set_param(instance, "CHORD_2", chord)
        self.set_param(instance, "NACA_Profile", naca)
        self.set_param(instance, "THICKNESS", thickness)
        self.set_param(instance, "SPAN", span)
        self.set_param(instance, "LOAD", load)
        self.set_param(instance, "TUBE_DIAMETER", tube_diameter)
        self.set_param(instance, "TUBE_OFFSET", tube_offset)
        self.set_param(instance, "TUBE_ROTATION", tube_rotation)
        self.set_param(instance, "TAPER_OFFSET", taper_offset)
        self.set_param(instance, "CONTROL_CHANNEL", channel)
        self.set_param(instance, "FLAP_BIAS", flap_bias)
        self.set_param(instance, "AILERON_BIAS", aileron_bias)
        self.set_param(instance, "SERVO_LENGTH", servo_length)
        self.set_param(instance, "SERVO_THICKNESS", servo_thickness)
        self.set_param(instance, "SERVO_WIDTH", servo_width)

        # Not connecting servo since it does not exist in UAV now
        if tube_inst:
            self.connect(instance, "Wing_Tube_Connector", tube_inst, tube_conn)

        return instance

    # Battery goes in the fuselage and is connected to the floor of the fuselage
    # There is a top and bottom connection, assuming that only
    # bottom connection is used.  top_bottom_conn is available to
    # change the connection to the top (for the creative option ;-))
    # top_bottom_conn: Top = 0, Bottom = 1 (default)
    def add_battery(
        self,
        model,
        rotation=0,
        top_bottom_conn=1,
        name=None,
        fuse_conn_num=None,
        mount_length=0,
        mount_width=0,
        controller_inst=None,
    ):

        top_bottom_conn = self.param_value(top_bottom_conn)
        assert top_bottom_conn in [0, 1]
        assert self.fuselage is not None

        instance = self.add_instance(model, name)
        self.set_param(instance, "ROTATION", rotation)

        fuse_conn_num = self.param_value(fuse_conn_num)
        connect_length_name = (
            "FLOOR_CONNECTOR_" + str(fuse_conn_num) + "_DISP_LENGTH"
        )
        connect_width_name = (
            "FLOOR_CONNECTOR_" + str(fuse_conn_num) + "_DISP_WIDTH"
        )
        self.set_param(self.fuselage, connect_length_name, mount_length)
        self.set_param(self.fuselage, connect_width_name, mount_width)

        floor_connect = "FloorConnector" + str(fuse_conn_num)
        if top_bottom_conn:
            self.connect(
                instance, "Bottom_Connector", self.fuselage, floor_connect
            )
        else:
            self.connect(
                instance, "Top_Connector", self.fuselage, floor_connect
            )

        if controller_inst:
            self.connect(instance, "PowerBus", controller_inst, "BatteryPower")

        return instance

    def add_motor(
        self,
        model,
        channel=0,
        name=None,
        mount_inst=None,
        mount_conn=None,
        controller_inst=None,
    ):
        instance = self.add_instance(model, name)
        self.set_param(instance, "CONTROL_CHANNEL", channel)

        if mount_inst:
            self.connect(instance, "Base_Connector", mount_inst, mount_conn)

        if controller_inst:
            self.connect(instance, "MotorPower", controller_inst, "MotorPower")

        return instance

    # Propeller configuration:
    # prop_type    direction    description
    #     1          1          CCW puller
    #    -1         -1          CW puller
    #     1         -1          CW pusher
    #    -1          1          CCW pusher
    def add_propeller(
        self,
        model,
        prop_type,
        direction,
        name=None,
        motor_inst=None,
    ):
        assert self.param_value(prop_type) in [-1, 1]
        assert self.param_value(direction) in [-1, 1]

        instance = self.add_instance(model, name)
        self.set_param(instance, "Prop_type", prop_type)
        self.set_param(instance, "Direction", direction)

        if motor_inst:
            self.connect(
                motor_inst, "Prop_Connector", instance, "MOTOR_CONNECTOR_CS_IN"
            )

        return instance

    # see propeller configuration above
    def add_motor_propeller(
        self,
        motor_model,
        prop_model,
        prop_type,
        direction,
        control_channel=0,
        name_prefix=None,
        mount_inst=None,
        mount_conn=None,
        controller_inst=None,
    ):
        motor_inst = self.add_motor(
            model=motor_model,
            channel=control_channel,
            name=name_prefix + "_motor" if name_prefix else None,
            mount_inst=mount_inst,
            mount_conn=mount_conn,
            controller_inst=controller_inst,
        )

        prop_inst = self.add_propeller(
            model=prop_model,
            name=name_prefix + "_prop" if name_prefix else None,
            prop_type=prop_type,
            direction=direction,
            motor_inst=motor_inst,
        )

        return motor_inst, prop_inst

    def close_design(self, orient_z_angle=90):
        assert self.client and self.design
        assert self.fuselage is not None

        orient = self.add_instance("Orient", "Orient")

        self.set_param(orient, "Z_ANGLE", orient_z_angle)
        self.connect(orient, "ORIENTCONN", self.main_hub, "Orient_Connector")

        self.client.orient_design(self.design, orient.name)

        print("Closing design", self.design)

        self.main_hub = None
        self.design = None

        self.client.close()
        self.client = None
