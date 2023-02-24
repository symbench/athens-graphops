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

#===============================================================================
# These functions are used to create UAM/UAV designs based on corpus
# components


import math
from typing import Optional, Tuple, Union, Any, List, Dict

from .query import Client
from .dataset import get_model_data


class Instance():
    def __init__(self, model: str, name: str):
        self.model = model
        self.name = name
        self.parameters = dict()


class StudyParam:
    """
    Study parameters used in a design setup. 
    `param_type` indicates if the study parameter is either: 
        ["Structural" | "FDM" | "CargoMass"]
        This helps with creation of the configuration (YAML) 
        and CSV files for random value studies.
    """
    def __init__(self, name, value, param_type):
        self.name = name
        self.value = value
        self.param_type = param_type
        
        
class Designer():
    def __init__(self):
        self.client = None

    def create_design(self, design: str):
        assert self.client is None
        self.client = Client()
        self.instances = dict()
        self.nextid = 1

        self.design = design
        print("Creating design", self.design)
        self.client.create_design(self.design)

        self.fuselage = None

    def generate_name(self) -> str:
        instance = "inst_{:04}".format(self.nextid)
        self.nextid += 1
        return instance

    def add_instance(self, model: str, name: Optional[str]) -> str:
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

    def connect(self, instance1: Instance, connector1: str,
                instance2: Instance, connector2: str):
        assert self.client and self.design
        assert isinstance(instance1, Instance) and isinstance(
            instance2, Instance)

        print("Creating connection from", instance1.name, connector1,
              "to", instance2.name, connector2)
        self.client.create_connection(
            self.design, instance1.name, connector1, instance2.name, connector2)

    def set_parameter(self, instance: Instance, param: str, value: Union[float, str]):
        assert self.client and self.design
        assert isinstance(instance, Instance)

        if not isinstance(value, StudyParam):
            param_name = instance.name + "_" + param
            self.client.create_parameter(self.design, param_name, value)
        else:
            param_name = value.name
        
        self.client.assign_parameter(
            self.design, instance.name, param, param_name)

    def set_study_param(self, param, value, param_type="Structural"):
        assert self.client and self.design
        self.client.create_parameter(self.design, param, value)
        return StudyParam(param, value, param_type)
    
    @classmethod
    def param_value(cls, param):
        if isinstance(param, StudyParam):
            return param.value
        return param
    
    # MM TODO: this is really set_study_param for a list of instances
    #          when architect designs are move to platform, this will mostly be removed
    #          see how json_designer uses this and if that function is kept
    def set_named_parameter(self, instance: List[Instance], named_param: str, param: str, value: Union[float, str], param_exist=False):
        if not param_exist:
            self.client.create_parameter(self.design, named_param, value)
        for inst in instance:
            assert isinstance(inst, Instance)
            self.client.assign_parameter(
                self.design, inst.name, param, named_param)

    # MM TODO: used for FDM parameters (can replace with set_study_param) and using in json_designer.py
    #          when architect designs are move to platform, this will mostly be removed
    #          see how json_designer uses this and if that function is kept
    def set_config_param(self, param: str, value: Union[float, str]):
        self.client.create_parameter(self.design, param, value)

    def add_fuselage_uam(self,
                         length: float,
                         sphere_diameter: float,
                         middle_length: float,
                         tail_diameter: float,
                         floor_height: float,
                         seat_1_fb: float,
                         seat_1_lr: float,
                         seat_2_fb: float,
                         seat_2_lr: float,
                         port_thickness: float = 100,
                         top_port_disp: float = 0,
                         bottom_port_disp: float = 0,
                         left_port_disp: float = 0,
                         right_port_disp: float = 0,
                         name: Optional[str] = None):
        """
        Note (10/2022): This was written when FUSE_SPHERE_CYL_CONE class existed along
        with FuselageNACA class.  But now only the FuselageNACA is available.
        The parameters/properties and connections are the same, so leaving this
        alone for now.  Plan to update when the program returns to UAM designs
        """
        assert self.fuselage is None
        assert self.param_value(floor_height) > 0

        instance = self.add_instance("FUSE_SPHERE_CYL_CONE", name)
        self.set_parameter(instance, "LENGTH", length)
        self.set_parameter(instance, "SPHERE_DIAMETER", sphere_diameter)
        self.set_parameter(instance, "MIDDLE_LENGTH", middle_length)
        self.set_parameter(instance, "TAIL_DIAMETER", tail_diameter)
        self.set_parameter(instance, "FLOOR_HEIGHT", floor_height)
        self.set_parameter(instance, "SEAT_1_FB", seat_1_fb)
        self.set_parameter(instance, "SEAT_1_LR", seat_1_lr)
        self.set_parameter(instance, "SEAT_2_FB", seat_2_fb)
        self.set_parameter(instance, "SEAT_2_LR", seat_2_lr)
        self.set_parameter(instance, "PORT_THICKNESS", port_thickness)
        self.set_parameter(instance, "TOP_PORT_DISP", top_port_disp)
        self.set_parameter(instance, "BOTTOM_PORT_DISP", bottom_port_disp)
        self.set_parameter(instance, "LEFT_PORT_DISP", left_port_disp)
        self.set_parameter(instance, "RIGHT_PORT_DISP", right_port_disp)

        self.fuselage = instance
        return instance

    def add_fuselage_uav(self,
                         floor_height: float,
                         fuse_width: float,
                         fuse_height: float,
                         fuse_cyl_length: float,
                         bottom_connector_offset_length: float = 0,
                         bottom_connector_offset_width: float = 0,
                         bottom_connector_rotation: float = 0,
                         name: Optional[str] = None):
        assert self.fuselage is None
        # provided by SwRI
        assert self.param_value(floor_height) > 0
        assert self.param_value(floor_height) < self.param_value(fuse_height)

        instance = self.add_instance("capsule_fuselage", name)
        self.set_parameter(instance, "FLOOR_HEIGHT", floor_height)
        self.set_parameter(instance, "HORZ_DIAMETER", fuse_width)
        self.set_parameter(instance, "VERT_DIAMETER", fuse_height)
        self.set_parameter(instance, "FUSE_CYL_LENGTH", fuse_cyl_length)
        self.set_parameter(
            instance, "BOTTOM_CONNECTOR_OFFSET_LENGTH", bottom_connector_offset_length)
        self.set_parameter(
            instance, "BOTTOM_CONNECTOR_OFFSET_WIDTH", bottom_connector_offset_width)
        self.set_parameter(
            instance, "BOTTOM_CONNECTOR_ROTATION", bottom_connector_rotation)

        self.fuselage = instance
        return instance

    def add_fuselage_uav_connects(self,
                                  connects: List[Dict[int, Any]] = None,
                                  mount_inst: List[Instance] = None,
                                  mount_conn: List[str] = None):
        """
        This defines how components are attached to the fuselage floor
        BottomConnector is attached when defining the "main_hub", so not included here
        Connects, mount_inst and mount_conn are lists that indicates:
            connects: which floor connection numbers to use  and the locations
                    key: number, values: length, width
            mount_inst: the component instance mounting to the connects (same size as connects list)
            mount_conn: the mount_inst connection (same size as connects list)
        NOTE: This function can be used if wanting to do all connects at once.
        Otherwise, connections can be indicated when creating instances of sensors
        and batteries which attach to the fuselage floor.
        """
        assert self.fuselage is not None

        for num in connects:
            connect_length_name = "FLOOR_CONNECTOR_" + \
                str(num) + "_DISP_LENGTH"
            connect_width_name = "FLOOR_CONNECTOR_" + str(num) + "_DISP_WIDTH"
            connect_name = "FloorConnector" + str(num)
            size_list = connects[num]
            self.set_parameter(
                self.fuselage, connect_length_name, size_list[0])
            self.set_parameter(self.fuselage, connect_width_name, size_list[1])
            self.connect(self.fuselage, connect_name,
                         mount_inst[num], mount_conn[num])

    ##################################
    # UAM specific components
    ##################################
    def add_cylinder(self,
                     length: float,
                     diameter: float,
                     port_thickness: float,
                     front_angle: float = 0,
                     name: Optional[str] = None,
                     mount_inst: Optional[Instance] = None,
                     mount_conn: Optional[str] = None) -> str:

        # observed requirements in CREO, but min port_thickness is flaky
        assert 8 <= self.param_value(port_thickness) < self.param_value(diameter) <= self.param_value(length)
        assert 0 <= self.param_value(front_angle <= 360)

        instance = self.add_instance("PORTED_CYL", name)
        self.set_parameter(instance, "DIAMETER", diameter)
        self.set_parameter(instance, "LENGTH", length)
        self.set_parameter(instance, "PORT_THICKNESS", port_thickness)
        self.set_parameter(instance, "FRONT_ANGLE", front_angle)

        if mount_inst:
            self.connect(instance, "FRONT_CONNECTOR",
                         mount_inst, mount_conn)

        return instance

    def add_flip_in(self,
                    diameter: float,
                    name: Optional[str] = None):
        instance = self.add_instance("Cyl_Flip", name)
        self.set_parameter(instance, "DIAMETER", diameter)

        return instance

    def add_flip_out(self,
                     diameter: float,
                     name: Optional[str] = None,
                     front_inst: Optional[Instance] = None,
                     front_conn: Optional[str] = None,
                     rear_inst: Optional[Instance] = None,
                     rear_conn: Optional[str] = None):
        instance = self.add_instance("Cyl_Flip_Out", name)
        self.set_parameter(instance, "DIAMETER", diameter)

        if front_inst:
            self.connect(instance, "Flip_Connector_1",
                         front_inst, front_conn)
        if rear_inst:
            self.connect(instance, "Flip_Connector_2",
                         rear_inst, rear_conn)

        return instance

    def add_passenger(self, name: Optional[str] = None,
                      fuselage_inst: Optional[Instance] = None,
                      fuselage_conn: Optional[str] = None) -> str:
        instance = self.add_instance("Passenger", name)
        if fuselage_inst:
            self.connect(instance, "Connector",
                         fuselage_inst, fuselage_conn)
        return instance

    ##################################
    # UAV specific components
    ##################################
    def add_cargo(self,
                  weight: StudyParam,
                  rotation: float = 0,
                  name: Optional[str] = None,
                  mount_inst: Optional[Instance] = None,
                  mount_conn: Optional[str] = None) -> Tuple[str, str]:
        """
        Add cargo and cargo case
        Expect weight to be a study parameter setup by the platform definition
        with the parameter name of "CargoMass"
        """
        # Only two weights are valid
        assert self.param_value(weight) in [0.001, 0.5]

        # Setup variable to allow .csv file to change the cargo mass
        instance_cargo = self.add_instance("Cargo", name)
        self.set_parameter(instance_cargo, "WEIGHT", weight)

        # add cargo case (for attachment)
        case_name = name + "_case"
        instance_case = self.add_instance("CargoCase", case_name)
        self.set_parameter(instance_case, "Rotation", rotation)

        # mount cargo in case
        self.connect(instance_case, "CargoConnector",
                     instance_cargo, "CargoConnector")

        # mount case to the fuselage
        if mount_inst:
            self.connect(instance_case, "Case2HubConnector",
                         mount_inst, mount_conn)

        return instance_cargo, instance_case

    def add_flange(self,
                   hole_diameter: float,
                   bottom_angle: int = 0,
                   side_angle: int = 0,
                   name: Optional[str] = None,
                   mount_top_inst: Optional[Instance] = None,
                   mount_top_conn: Optional[str] = None,
                   mount_bottom_inst: Optional[Instance] = None,
                   mount_bottom_conn: Optional[str] = None,
                   mount_side_inst: Optional[Instance] = None,
                   mount_side_conn: Optional[str] = None) -> str:
        """
        Only 3 flange options (0281, 0394, 05) are valid
        Tubes (of the same size as flange) are inserted into the flange
        """
        # models to hole (tube OD) sizes
        flange_models = {
            "0281_para_flange": 7.1374,
            "0394_para_flange": 10.0076,
            "05OD_para_flange": 12.7
        }
        
        if isinstance(hole_diameter, StudyParam):
            print("WARNING: flange hole dia is a study parameter (fixed CAD part)")
            hole_diameter = self.param_value(hole_diameter)

        for flange_model, flange_hole_diameter in flange_models.items():
            if math.isclose(hole_diameter, flange_hole_diameter, rel_tol=1e-3):
                break
        else:
            raise ValueError("Invalid flange hole diameter", hole_diameter)
        
        instance = self.add_instance(flange_model, name)
        self.set_parameter(instance, "BOTTOM_ANGLE", bottom_angle)
        self.set_parameter(instance, "SIDE_ANGLE", side_angle)

        if mount_top_inst:
            self.connect(instance, "TopConnector",
                         mount_top_inst, mount_top_conn)
        if mount_bottom_inst:
            self.connect(instance, "BottomConnector",
                         mount_bottom_inst, mount_bottom_conn)
        if mount_side_inst:
            self.connect(instance, "SideConnector",
                         mount_side_inst, mount_side_conn)

        return instance

    def add_tube(self,
                 od: float,
                 length: float,
                 base_rotation: int = 0,
                 end_rotation: int = 0,
                 offset_1: float = 0,
                 offset_2: float = 0,
                 name: Optional[str] = None,
                 mount_base_inst: Optional[Instance] = None,
                 mount_base_conn: Optional[str] = None,
                 mount_end_inst: Optional[Instance] = None,
                 mount_end_conn: Optional[str] = None) -> str:
        """
        Only 3 tube options (0281, 0394, 05) are valid
        """
        # models to tube OD sizes
        tube_models = {
            "0281OD_para_tube": 7.1374,
            "0394OD_para_tube": 10.0076,
            "05OD_para_tube": 12.7,
        }
 
        if isinstance(od, StudyParam):
            print("WARNING: tube OD is a study parameter (fixed CAD part)")
            od = self.param_value(od)

        for tube_model, tube_od in tube_models.items():
            if math.isclose(od, tube_od, rel_tol=1e-3):
                break
        else:
            raise ValueError("Invalid tube OD", od)

        instance = self.add_instance(tube_model, name)
        self.set_parameter(instance, "Length", length)

        # larger sizes do not have these parameters
        self.set_parameter(instance, "BASE_ROT", base_rotation)
        self.set_parameter(instance, "END_ROT", end_rotation)
        self.set_parameter(instance, "Offset1", offset_1)
        self.set_parameter(instance, "Offset2", offset_2)

        if mount_base_inst:
            self.connect(instance, "BaseConnection",
                         mount_base_inst, mount_base_conn)
        if mount_end_inst:
            self.connect(instance, "EndConnection",
                         mount_end_inst, mount_end_conn)

        return instance

    def add_hub(self,
                num_connects: int,
                diameter: float = 10.0076,
                connector_horizonal_angle: int = 120,
                connector_vertical_angle: int = 0,
                name: Optional[str] = None,
                connects: Optional[List[str]] = None,
                mount_inst: Optional[List[Instance]] = None,
                mount_conn: Optional[List[str]] = None,
                orient_base: Optional[bool] = False) -> str:
        """
        5 hub options
        Connects, mount_inst and mount_conn are lists that indicates:
            connects: which hub connections to use
            mount_inst: the component instance mounting to the connects  (same size as connects list)
            mount_conn: the mount_inst connection  (same size as connects list)
            orient_base is a bool to identify which hub is the main_hub that connects
              to Orient in the close_design function, true make it as the main_hub
        """
        assert(2 <= self.param_value(num_connects) <= 6)
        hub_model = "0394od_para_hub_" + str(num_connects)
        instance = self.add_instance(hub_model, name)
        self.set_parameter(instance, "DIAMETER", diameter)
        self.set_parameter(instance, "ANGHORZCONN", connector_horizonal_angle)
        self.set_parameter(instance, "ANGVERTCONN", connector_vertical_angle)

        if connects:
            assert mount_inst and len(connects) == len(mount_inst)
            assert mount_conn and len(connects) == len(mount_conn)
            
            for i in range(len(connects)):
                self.connect(instance, connects[i],
                             mount_inst[i], mount_conn[i])

        # main_hub will be where the connection to Orient occurs
        if orient_base == True:
            self.main_hub = instance

        return instance

    def add_sensor(self,
                   sensor_model: str,
                   rotation: float = 0,
                   name: Optional[str] = None,
                   mount_conn_num: Optional[int] = None,
                   mount_length: Optional[float] = 0,
                   mount_width: Optional[float] = 0) -> str:
        """
        6 sensor options
        If indicating mount connection number, also indicate the mount_length and mount_width
        to allow connector placement on the fuselage floor
        """
        assert self.fuselage is not None

        instance = self.add_instance(sensor_model, name)
        self.set_parameter(instance, "ROTATION", rotation)

        mount_conn_num = self.param_value(mount_conn_num)
        if mount_conn_num:
            connect_length_name = "FLOOR_CONNECTOR_" + \
                str(mount_conn_num) + "_DISP_LENGTH"
            connect_width_name = "FLOOR_CONNECTOR_" + \
                str(mount_conn_num) + "_DISP_WIDTH"
            connect_name = "FloorConnector" + str(mount_conn_num)
            self.set_parameter(
                self.fuselage, connect_length_name, mount_length)
            self.set_parameter(self.fuselage, connect_width_name, mount_width)
            self.connect(instance, "SensorConnector",
                         self.fuselage, connect_name)

        return instance

    ##################################
    # Common components
    ##################################
    def add_battery_controller(self, name: Optional[str] = None) -> str:
        instance = self.add_instance("BatteryController", name)
        return instance

    def add_wing_uam(self,
                     naca: str,
                     chord: float,
                     span: float,
                     load: float,
                     name: Optional[str] = None,
                     left_inst: Optional[Instance] = None,
                     left_conn: Optional[str] = None,
                     right_inst: Optional[Instance] = None,
                     right_conn: Optional[str] = None):
        assert len(self.param_value(naca)) == 4 
        assert self.param_value(chord) >= 1 
        assert self.param_value(span) >= 1
        assert self.param_value(load) >= 1
        
        thickness = int(self.param_value(naca[2:4]))

        instance = self.add_instance("naca_wing", name)
        self.set_parameter(instance, "NACA_Profile", naca)
        self.set_parameter(instance, "THICKNESS", thickness)
        self.set_parameter(instance, "CHORD_1", chord)
        self.set_parameter(instance, "CHORD_2", chord)
        self.set_parameter(instance, "SPAN", span)
        self.set_parameter(instance, "LOAD", load)

        if left_inst:
            self.connect(instance, "Connector_1", left_inst, left_conn)

        if right_inst:
            self.connect(instance, "Connector_2", right_inst, right_conn)

        return instance

    def add_wing_uav(self,
                     direction: str,
                     chord: float,
                     span: float,
                     thickness: float,
                     naca: str,
                     load: float = 15,
                     tube_diameter: float = 10,
                     tube_offset: float = 100,
                     tube_rotation: float = 0,
                     taper_offset: float = 0,
                     channel: int = 0,
                     flap_bias: float = 0.5,
                     aileron_bias: float = 0.5,
                     servo_length: float = 0.1,
                     servo_thickness: float = 0.1,
                     servo_width: float = 0.1,
                     name: Optional[str] = None,
                     tube_inst: Optional[Instance] = None,
                     tube_conn: Optional[str] = None):
        assert len(self.param_value(naca)) == 4
        assert self.param_value(chord) >= 1
        assert self.param_value(span) >= 1
        assert self.param_value(load) >= 1
        direction = self.param_value(direction)
        assert direction in ["Horizontal", "Vertical"]
        thickness = int(self.param_value(naca[2:4]))

        if direction == "Horizontal":
            instance = self.add_instance("Wing_horiz_hole", name)
        elif direction == "Vertical":
            instance = self.add_instance("Wing_vert_hole", name)

        self.set_parameter(instance, "CHORD_1", chord)
        self.set_parameter(instance, "CHORD_2", chord)
        self.set_parameter(instance, "NACA_Profile", naca)
        self.set_parameter(instance, "THICKNESS", thickness)
        self.set_parameter(instance, "SPAN", span)
        self.set_parameter(instance, "LOAD", load)
        self.set_parameter(instance, "TUBE_DIAMETER", tube_diameter)
        self.set_parameter(instance, "TUBE_OFFSET", tube_offset)
        self.set_parameter(instance, "TUBE_ROTATION", tube_rotation)
        self.set_parameter(instance, "TAPER_OFFSET", taper_offset)
        self.set_parameter(instance, "CONTROL_CHANNEL", channel)
        self.set_parameter(instance, "FLAP_BIAS", flap_bias)
        self.set_parameter(instance, "AILERON_BIAS", aileron_bias)
        self.set_parameter(instance, "SERVO_LENGTH", servo_length)
        self.set_parameter(instance, "SERVO_THICKNESS", servo_thickness)
        self.set_parameter(instance, "SERVO_WIDTH", servo_width)

        # Not connecting servo since it does not exist in UAV now
        if tube_inst:
            self.connect(instance, "Wing_Tube_Connector", tube_inst, tube_conn)

        return instance

    def add_battery_uam(self, model: str,
                        naca: str,
                        chord: float,
                        span: float,
                        mount_side: int,
                        voltage_request: float,
                        volume_percent: float,
                        name: Optional[str] = None,
                        wing_inst: Optional[Instance] = None,
                        controller_inst: Optional[Instance] = None):
        assert len(self.param_value(naca)) == 4
        assert self.param_value(chord) >= 1 
        assert self.param_value(span) >= 1
        assert self.param_value(mount_side) in [1, 2]
        assert 0 <= self.param_value(volume_percent) <= 100
        thickness = int(self.param_value(naca[2:4]))

        instance = self.add_instance(model, name)
        self.set_parameter(instance, "THICKNESS", thickness)
        self.set_parameter(instance, "CHORD_1", chord)
        self.set_parameter(instance, "CHORD_2", chord)
        self.set_parameter(instance, "SPAN", span)
        self.set_parameter(instance, "MOUNT_SIDE", mount_side)
        self.set_parameter(instance, "VOLTAGE_REQUEST", voltage_request)
        self.set_parameter(instance, "VOLUME_PERCENT", volume_percent)

        if wing_inst:
            if mount_side == 1:
                self.connect(instance, "Battery_Connector_1_out",
                             wing_inst, "Battery_Connector_1")
            else:
                self.connect(instance, "Battery_Connector_2_out",
                             wing_inst, "Battery_Connector_2")

        if controller_inst:
            self.connect(instance, "PowerBus",
                         controller_inst, "BatteryPower")

        return instance

    def add_battery_uav(self, model: str,
                        rotation: int = 0,
                        top_bottom_conn: int = 1,
                        name: Optional[str] = None,
                        fuse_conn_num: Optional[int] = None,
                        mount_length: Optional[float] = 0,
                        mount_width: Optional[float] = 0,
                        controller_inst: Optional[Instance] = None) -> str:
        """
        Battery goes in the fuselage and is connected to the floor of the fuselage
        There is a top and bottom connection, assuming that only
        bottom connection is used.  top_bottom_conn is available to
        change the connection to the top (for the creative option ;-))
        top_bottom_conn: Top = 0, Bottom = 1 (default)
        """
        top_bottom_conn = self.param_value(top_bottom_conn)
        assert top_bottom_conn in [0, 1]
        assert self.fuselage is not None

        instance = self.add_instance(model, name)
        self.set_parameter(instance, "ROTATION", rotation)

        fuse_conn_num = self.param_value(fuse_conn_num)
        connect_length_name = "FLOOR_CONNECTOR_" + \
            str(fuse_conn_num) + "_DISP_LENGTH"
        connect_width_name = "FLOOR_CONNECTOR_" + \
            str(fuse_conn_num) + "_DISP_WIDTH"
        self.set_parameter(self.fuselage, connect_length_name, mount_length)
        self.set_parameter(self.fuselage, connect_width_name, mount_width)

        floor_connect = "FloorConnector" + str(fuse_conn_num)
        if top_bottom_conn:
            self.connect(instance, "Bottom_Connector",
                         self.fuselage, floor_connect)
        else:
            self.connect(instance, "Top_Connector",
                         self.fuselage, floor_connect)

        if controller_inst:
            self.connect(instance, "PowerBus",
                         controller_inst, "BatteryPower")

        return instance

    def add_motor(self, model: str,
                  channel: int = 0,
                  name: Optional[str] = None,
                  mount_inst: Optional[Instance] = None,
                  mount_conn: Optional[str] = None,
                  controller_inst: Optional[Instance] = None):
        instance = self.add_instance(model, name)
        self.set_parameter(instance, "CONTROL_CHANNEL", channel)

        if mount_inst:
            self.connect(instance, "Base_Connector",
                         mount_inst, mount_conn)

        if controller_inst:
            self.connect(instance, "MotorPower",
                         controller_inst, "MotorPower")

        return instance

    def add_propeller(self, model: str,
                      prop_type: int,
                      direction: int,
                      name: Optional[str] = None,
                      motor_inst: Optional[Instance] = None):
        """
        Propeller configuration:
        prop_type    direction    description
            1          1          CCW puller
           -1         -1          CW puller
            1         -1          CW pusher
           -1          1          CCW pusher
        """
        assert self.param_value(prop_type) in [-1, 1] 
        assert self.param_value(direction) in [-1, 1]

        instance = self.add_instance(model, name)
        self.set_parameter(instance, "Prop_type", prop_type)
        self.set_parameter(instance, "Direction", direction)

        if motor_inst:
            self.connect(motor_inst, "Prop_Connector",
                         instance, "MOTOR_CONNECTOR_CS_IN")

        return instance

    def add_motor_propeller(self,
                            motor_model: str,
                            prop_model: str,
                            prop_type: int,
                            direction: int,
                            control_channel: int = 0,
                            name_prefix: Optional[str] = None,
                            mount_inst: Optional[Instance] = None,
                            mount_conn: Optional[str] = None,
                            controller_inst: Optional[Instance] = None):
        motor_inst = self.add_motor(
            model=motor_model,
            channel=control_channel,
            name=name_prefix + "_motor" if name_prefix else None,
            mount_inst=mount_inst,
            mount_conn=mount_conn,
            controller_inst=controller_inst)

        prop_inst = self.add_propeller(
            model=prop_model,
            name=name_prefix + "_prop" if name_prefix else None,
            prop_type=prop_type,
            direction=direction,
            motor_inst=motor_inst,
        )

        return motor_inst, prop_inst

    def close_design(self,
                     corpus: str = "uam",
                     orient_z_angle: int = 90):
        assert self.client and self.design
        assert self.fuselage is not None

        orient = self.add_instance("Orient", "Orient")
        if corpus == "uam":
            self.connect(orient, "ORIENTCONN", self.fuselage, "ORIENT")
        # uav corpus
        else:
            self.set_parameter(orient, "Z_ANGLE", orient_z_angle)
            self.connect(orient, "ORIENTCONN",
                         self.main_hub, "Orient_Connector")

        self.client.orient_design(self.design, orient.name)

        print("Closing design", self.design)
        if corpus == "uam":
            self.fuselage = None
        else:
            self.main_hub = None
        self.design = None

        self.client.close()
        self.client = None


def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    args = parser.parse_args(args)


if __name__ == '__main__':
    run()
