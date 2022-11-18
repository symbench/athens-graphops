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


#from distutils.command.build_scripts import first_line_re
from distutils.command.config import config
from typing import Any, Dict, List, Optional
from .designer import Designer
from . import CONFIG
from .workflow import JenkinsClient
from .query import Client
from .dataset import get_component_parameters
from .dataset import random_component_selection
from .dataset import randomize_parameters
#from .dataset import random_naca_profile_selection
from .dataset import get_corpus_assigned_parameters
from .dataset import randomize_cyl_length
from .dataset import CORPUS_DATA, BATTERY_TABLE, MOTOR_TABLE, PROPELLER_TABLE
import random
import math
import creopyson


class Architect():
    def __init__(self):
        self.client = None
        self.jenkins_client = None
        self.creoson_client = None

    def open_jenkins_client(self, workflow="UAM_Workflows"):
        """Prepare for Jenkins runs for each design. Design name will be updated in loop."""
        assert self.jenkins_client is None
        jenkins_url = "http://" + CONFIG["hostname"] + ":8080"
        print("Jenkins URL: %s" % jenkins_url)
        print("Jenkins Username: %s" % CONFIG["jenkinsuser"])
        print("Jenkins Password: %s" % CONFIG["jenkinspwd"])
        self.jenkins_client = JenkinsClient(
            jenkins_url, CONFIG["jenkinsuser"], CONFIG["jenkinspwd"])

        self.workflow = workflow
        if (self.workflow == "UAM_Workflows") or (self.workflow == "UAV_Workflows"):
            self.jenkins_parameters = {
                "graphGUID": "Rake",
                "PETName": "/D_Testing/PET/FlightDyn_V2_AllPaths",
                "NumSamples": "1",
                "DesignVars": "Analysis_Type=3,3"
            }
        elif (self.workflow == "uam_direct2cad"):
            self.jenkins_parameters = {
                "graphGUID": "Rake",
                "minioBucket": "graphops",
                "paramFile": "rand_design_runs.csv",
                "resultsFileName": "results123"
            }
            self.fdm_parameters = {
                "Analysis_Type": 3,
                "Flight_Path": [1, 3, 4, 5],
                "Requested_Lateral_Speed": 1,
                "Requested_Vertical_Speed": 19,
                "Q_Position": 1,
                "Q_Velocity": 1,
                "Q_Angular_Velocity": 1,
                "Q_Angles": 1,
                "Ctrl_R": 0.1
            }

    def set_fdm_parameters(self, parameters: Dict[str, Any]):
        self.fdm_parameters = parameters

    def open_query_client(self):
        """Open a query client (gremlin) to grab the graph design information"""
        assert self.client is None
        self.client = Client()

    def update_parameters(self, key_name: str, value: str):
        """Update any of the Jenkins Workflow Input Parameters"""
        self.jenkins_parameters[key_name] = value

    def close_client(self):
        """Close GraphDB Client"""
        assert self.client is not None
        print("Closing query client")
        self.client.close()
        self.client = None

    def close_jenkins_client(self):
        """Close Jenkins Client"""
        assert self.jenkins_client is not None
        print("Closing Jenkins client")
        self.jenkins_client = None

    def connect_creoson_server(self):
        """Connect to Creoson Server for using with uam_direct2cad Workflow"""
        assert self.creoson_client is None
        creoson_ip = CONFIG["hostname"]
        #creoson_ip = "localhost"
        creason_port = 9056

        self.creoson_client = creopyson.Client(
            ip_adress=creoson_ip, port=creason_port)
        self.creoson_client.connect()
        print("Started Creoson Server - SessionID: %s" %
              self.creoson_client.sessionId)

    def start_creo(self):
        """Start CREOSON using the Creoson Server"""
        # This ties the execution of the command to the computer running the server
        # MM TODO: need to find a way to remotely start this (or if already works remotely)
        nitro_proe_remote_loc = "C:\\jwork\\nitro_proe_remote.bat"
        #nitro_proe_remote_loc = None
        creo_version = 5
        use_desktop = False

        if not self.creoson_client.is_creo_running():
            self.creoson_client.start_creo(
                nitro_proe_remote_loc, use_desktop=use_desktop)
            print("CREO started")
        # if creo_version >= 7:
        #    self.creoson_client.creo_set_creo_version(creo_version)

    def stop_creoson(self):
        """Stop the Creoson between runs"""
        assert self.creoson_client is not None
        if self.creoson_client.is_creo_running():
            print("Try stopping creoson")
            try:
                self.creoson_client.stop_creo()
                print("Stopping Creoson")
            except:
                self.creoson_client.kill_creo()
                print("Killed CREO using Creoson Server")

    def disconnect_creoson_server(self):
        """Stop the Creoson Server between runs"""
        assert self.creoson_client is not None
        self.creoson_client.disconnect()
        print("Disconnect from Creoson server")
        self.creoson_client = None

    def is_creo_running(self):
        """Check if CREO is running."""
        return self.creoson_client.is_creo_running()

    # Not sure this is needed yet
    # def restart_creoson_server(self):
    #    """ToDo: Remove HardCode"""
    #    p = subprocess.Popen(["restart_creoson.bat"], shell=False)
    #    time.sleep(2)


def randomize_existing_design(config_file: str, workflow: str, minio_bucket=''):
    """
    Given an existing design graph (in Janusgraph), randomize parameters that are defined in a yaml file.

    At this point, it is expected that the config yaml files are located in the athens_graphops configs folder.
    There is an example of the format - default_study_params.yaml
    This run uses the uam_direct2cad workflow.
    """
    # Setup Gremlin query and Jenkins interfaces
    architecture = Architect()
    architecture.open_jenkins_client(workflow)

    if (minio_bucket != ''):
        architecture.update_parameters("minioBucket", minio_bucket)
    else:
        minio_bucket = architecture.jenkins_parameters.get("minioBucket")

    # Convert yaml config file into csv file that indicates the parameter study desired.
    # The desired design name is in the config file, so it is returned for reference here.
    design_name_inst = architecture.jenkins_client.create_direct2cad_csv(
        minio_bucket, config_file)
    print("Design Name to test: {}".format(design_name_inst))

    # Run UAM_Workflow on the yaml specified design
    architecture.update_parameters("graphGUID", design_name_inst)
    param_filename = config_file.replace(".yaml", ".csv")
    architecture.update_parameters("paramFile", param_filename)
    result_filename = config_file.replace(".yaml", ".zip")
    architecture.update_parameters("resultsFileName", result_filename)
    print("Jenkins Parameter: {}".format(architecture.jenkins_parameters))

    build = architecture.jenkins_client.build_and_wait(
        workflow, architecture.jenkins_parameters)
    architecture.jenkins_client.save_results_from_build(
        build, design_name_inst)

    # Create json of all design information and add it to the Jenkins data.zip file
    architecture.open_query_client()
    design_json = architecture.client.get_design_data(design_name_inst)
    architecture.jenkins_client.add_design_json_to_results(
        design_name_inst, design_json)

    # For runs where the study CSV file is used, the partMass.json and partLocs.json are
    # only the last run, so skip collecting these for now
    # For uam_direct2cad, grab the partMass.json and partLocs.json files from the workflow directory
    # and add it to the data.zip
    # if workflow == "uam_direct2cad":
    #    architecture.jenkins_client.grab_extra_jsons_direct2cad(
    #        design_name_inst)
    # In between runs, creoson should be stopped and started again, so stopping here
    # architecture.stop_creoson()

    architecture.close_client()
    architecture.close_jenkins_client()
    # architecture.disconnect_creoson_server()


def create_minimal_uam():
    """
    This is for the UAM corpus.
    """
    designer = Designer()
    designer.create_design("Minimal")
    designer.add_fuselage_uam(name="fuselage",
                              length=2000,
                              sphere_diameter=1520,
                              middle_length=300,
                              tail_diameter=200,
                              floor_height=150,
                              seat_1_fb=1000,
                              seat_1_lr=-210,
                              seat_2_fb=1000,
                              seat_2_lr=210)
    designer.close_design()


def create_minimal_uav():
    """
    Create a minimal design (does not include uam_direct2cad workflow at this time, 
    it only creates the graph design).    
    """
    designer = Designer()
    designer.create_design("Minimal")
    fuselage = designer.add_fuselage_uav(name="fuselage",
                                         floor_height=20,
                                         fuse_width=190,
                                         fuse_height=125,
                                         fuse_cyl_length=270,
                                         bottom_connector_rotation=45)
    cargo, cargo_case = designer.add_cargo(weight=0.001,
                                           name="cargo")

    # Require main_hub for connection to Orient
    # Create hub connection lists (size of num_connections max)
    # Not all connections are needed
    designer.add_hub(name="main_hub",
                     num_connects=3,
                     connector_horizonal_angle=90,
                     connects=["Top_Connector", "Bottom_Connector"],
                     mount_inst=[fuselage, cargo_case],
                     mount_conn=["BottomConnector", "Case2HubConnector"],
                     orient_base=True)
    # Add batteries
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

    # Add sensors
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
    designer.close_design(corpus="uav", orient_z_angle=45)


def create_new_axe_cargo():
    """
    Recreating NewAxe_Cargo design (does not include uam_direct2cad workflow at this time, 
    it only creates the graph design).
    """
    designer = Designer()
    designer.create_design("NewAxeCargo")
    fuselage = designer.add_fuselage_uav(name="fuselage",
                                         floor_height=20,
                                         fuse_width=300,
                                         fuse_height=105,
                                         fuse_cyl_length=150,
                                         bottom_connector_rotation=90)
    cargo, cargo_case = designer.add_cargo(weight=0.5,
                                           name="cargo")

    # Require main_hub for connection to Orient
    # Create hub connection lists (size of num_connections max)
    # Not all connections are needed
    hub_main = designer.add_hub(name="main_hub",
                                num_connects=3,
                                connector_horizonal_angle=90,
                                connects=["Top_Connector", "Bottom_Connector"],
                                mount_inst=[fuselage, cargo_case],
                                mount_conn=["BottomConnector",
                                            "Case2HubConnector"],
                                orient_base=True)
    # Add batteries
    battery_control = designer.add_battery_controller(name="BatteryController")
    designer.add_battery_uav(model="TurnigyGraphene6000mAh6S75C",
                             name="Battery_1",
                             fuse_conn_num=2,
                             mount_length=0,
                             mount_width=-70,
                             controller_inst=battery_control)

    designer.add_battery_uav(model="TurnigyGraphene6000mAh6S75C",
                             name="Battery_2",
                             fuse_conn_num=1,
                             mount_length=0,
                             mount_width=70,
                             controller_inst=battery_control)

    # Add sensors
    designer.add_sensor(sensor_model="RpmTemp",
                        name="RpmTemp",
                        mount_conn_num=3,
                        mount_length=-20,
                        mount_width=33)
    designer.add_sensor(sensor_model="Current",
                        name="Current",
                        mount_conn_num=4,
                        mount_length=-20,
                        mount_width=-30)
    designer.add_sensor(sensor_model="Autopilot",
                        name="Autopilot",
                        mount_conn_num=5,
                        mount_length=50,
                        mount_width=0)
    designer.add_sensor(sensor_model="Voltage",
                        name="Voltage",
                        mount_conn_num=6,
                        mount_length=-20,
                        mount_width=11)
    designer.add_sensor(sensor_model="GPS",
                        name="GPS",
                        mount_conn_num=7,
                        mount_length=-80,
                        mount_width=0)
    designer.add_sensor(sensor_model="Variometer",
                        name="Variometer",
                        mount_conn_num=8,
                        mount_length=-20,
                        mount_width=-11)

    # Create front propellers section
    # Start at main hub, connect tubes on sides to side hubs,
    # then front flange and rail attach to propellers/motors
    mid_tube_l = designer.add_tube(size="0394",
                                   length=140,
                                   end_rotation=180,
                                   name="mid_tube_l",
                                   mount_base_inst=hub_main,
                                   mount_base_conn="Side_Connector_3")
    mid_tube_r = designer.add_tube(size="0394",
                                   length=140,
                                   name="mid_tube_r",
                                   mount_base_inst=hub_main,
                                   mount_base_conn="Side_Connector_1")
    side_hub_l = designer.add_hub(name="side_hub_l",
                                  num_connects=3,
                                  connector_horizonal_angle=90,
                                  connects=["Side_Connector_2"],
                                  mount_inst=[mid_tube_l],
                                  mount_conn=["EndConnection"])
    side_hub_r = designer.add_hub(name="side_hub_r",
                                  num_connects=3,
                                  connector_horizonal_angle=90,
                                  connects=["Side_Connector_2"],
                                  mount_inst=[mid_tube_r],
                                  mount_conn=["EndConnection"])
    front_rail_l = designer.add_tube(size="0394",
                                     length=335,
                                     end_rotation=270,
                                     name="front_rail_l",
                                     mount_base_inst=side_hub_l,
                                     mount_base_conn="Side_Connector_3")
    front_rail_r = designer.add_tube(size="0394",
                                     length=335,
                                     end_rotation=90,
                                     name="front_rail_r",
                                     mount_base_inst=side_hub_r,
                                     mount_base_conn="Side_Connector_3")
    front_flange_l = designer.add_flange(size="0394",
                                         name="front_flange_l",
                                         mount_bottom_inst=front_rail_l,
                                         mount_bottom_conn="EndConnection"
                                         )
    front_flange_r = designer.add_flange(size="0394",
                                         bottom_angle=90,
                                         name="front_flange_r",
                                         mount_bottom_inst=front_rail_r,
                                         mount_bottom_conn="EndConnection"
                                         )
    designer.add_motor_propeller(motor_model="kde_direct_KDE2315XF_885",
                                 prop_model="apc_propellers_7x5E",
                                 prop_type=-1,
                                 direction=-1,
                                 control_channel=1,
                                 name_prefix="front_l",
                                 mount_inst=front_flange_l,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    designer.add_motor_propeller(motor_model="kde_direct_KDE2315XF_885",
                                 prop_model="apc_propellers_7x5E",
                                 prop_type=1,
                                 direction=1,
                                 control_channel=2,
                                 name_prefix="front_r",
                                 mount_inst=front_flange_r,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    # Add front wings
    Front_Wing_Tube_Length = 52
    front_wing_tube_l = designer.add_tube(size="0394",
                                          length=Front_Wing_Tube_Length,
                                          name="front_wing_tube_l",
                                          mount_base_inst=front_flange_l,
                                          mount_base_conn="SideConnector")
    front_wing_tube_r = designer.add_tube(size="0394",
                                          length=Front_Wing_Tube_Length,
                                          name="front_wing_tube_r",
                                          mount_base_inst=front_flange_r,
                                          mount_base_conn="SideConnector")
    NACA_profile = "0012"
    front_wing_span = 450
    front_wing_chord = 150
    wing_thickness = 12
    front_tube_rotation = 180
    # Note: the autograph for the seed design indicates a tube_rotation of 180 for left wing, 90 looks more correct (MM)
    designer.add_wing_uav(direction="Vertical",
                          chord=front_wing_chord,
                          span=front_wing_span,
                          thickness=wing_thickness,
                          load=15,
                          naca=NACA_profile,
                          tube_offset=289.68,
                          tube_rotation=front_tube_rotation,
                          channel=5,
                          name="front_left_wing",
                          tube_inst=front_wing_tube_l,
                          tube_conn="EndConnection")
    designer.add_wing_uav(direction="Vertical",
                          chord=front_wing_chord,
                          span=front_wing_span,
                          thickness=wing_thickness,
                          load=15,
                          naca=NACA_profile,
                          tube_offset=160.32,
                          tube_rotation=front_tube_rotation,
                          channel=6,
                          name="front_right_wing",
                          tube_inst=front_wing_tube_r,
                          tube_conn="EndConnection")

    # Add rear wings
    Rear_Rail_Length = 220
    rear_rail_l = designer.add_tube(size="0394",
                                    length=Rear_Rail_Length,
                                    end_rotation=90,
                                    name="rear_rail_l",
                                    mount_base_inst=side_hub_l,
                                    mount_base_conn="Side_Connector_1")
    rear_rail_r = designer.add_tube(size="0394",
                                    length=Rear_Rail_Length,
                                    end_rotation=90,
                                    name="rear_rail_r",
                                    mount_base_inst=side_hub_r,
                                    mount_base_conn="Side_Connector_1")
    rear_hub_l = designer.add_hub(name="rear_hub_l",
                                  num_connects=3,
                                  connector_horizonal_angle=90,
                                  connects=["Side_Connector_1"],
                                  mount_inst=[rear_rail_l],
                                  mount_conn=["EndConnection"])
    rear_hub_r = designer.add_hub(name="rear_hub_r",
                                  num_connects=3,
                                  connector_horizonal_angle=90,
                                  connects=["Side_Connector_3"],
                                  mount_inst=[rear_rail_r],
                                  mount_conn=["EndConnection"])
    bottom_leg_l = designer.add_tube(size="0394",
                                     length=150,
                                     name="bottom_leg_l",
                                     mount_base_inst=rear_hub_l,
                                     mount_base_conn="Side_Connector_3")
    bottom_leg_r = designer.add_tube(size="0394",
                                     length=150,
                                     name="bottom_leg_r",
                                     mount_base_inst=rear_hub_r,
                                     mount_base_conn="Side_Connector_1")
    vertical_l = designer.add_tube(size="0394",
                                   length=150,
                                   end_rotation=90,
                                   offset_1=90,
                                   name="vertical_l",
                                   mount_base_inst=rear_hub_l,
                                   mount_base_conn="Side_Connector_2")
    vertical_r = designer.add_tube(size="0394",
                                   length=150,
                                   end_rotation=270,
                                   offset_1=90,
                                   name="vertical_r",
                                   mount_base_inst=rear_hub_r,
                                   mount_base_conn="Side_Connector_2")
    rear_wing_span = 609
    rear_wing_chord = 180
    designer.add_wing_uav(direction="Vertical",
                          chord=rear_wing_chord,
                          span=rear_wing_span,
                          thickness=wing_thickness,
                          naca=NACA_profile,
                          tube_offset=448.68,
                          tube_rotation=270,
                          channel=8,
                          name="rear_left_wing",
                          tube_inst=vertical_l,
                          tube_conn="OffsetConnection1")
    designer.add_wing_uav(direction="Vertical",
                          chord=rear_wing_chord,
                          span=rear_wing_span,
                          thickness=wing_thickness,
                          naca=NACA_profile,
                          tube_offset=160.32,
                          tube_rotation=90,
                          channel=7,
                          name="rear_right_wing",
                          tube_inst=vertical_r,
                          tube_conn="OffsetConnection1")
    rear_flange_l = designer.add_flange(size="0394",
                                        name="rear_flange_l",
                                        mount_side_inst=vertical_l,
                                        mount_side_conn="EndConnection"
                                        )
    rear_flange_r = designer.add_flange(size="0394",
                                        name="rear_flange_r",
                                        mount_side_inst=vertical_r,
                                        mount_side_conn="EndConnection"
                                        )
    designer.add_motor_propeller(motor_model="kde_direct_KDE2315XF_885",
                                 prop_model="apc_propellers_7x5E",
                                 prop_type=-1,
                                 direction=-1,
                                 control_channel=3,
                                 name_prefix="rear_l",
                                 mount_inst=rear_flange_l,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    designer.add_motor_propeller(motor_model="kde_direct_KDE2315XF_885",
                                 prop_model="apc_propellers_7x5E",
                                 prop_type=1,
                                 direction=1,
                                 control_channel=4,
                                 name_prefix="rear_r",
                                 mount_inst=rear_flange_r,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    Top_Leg_Tube_Length = 150.1524
    top_leg_l = designer.add_tube(size="0394",
                                  length=Top_Leg_Tube_Length,
                                  name="top_leg_l",
                                  mount_base_inst=rear_flange_l,
                                  mount_base_conn="BottomConnector")
    top_leg_r = designer.add_tube(size="0394",
                                  length=Top_Leg_Tube_Length,
                                  name="top_leg_r",
                                  mount_base_inst=rear_flange_r,
                                  mount_base_conn="BottomConnector")

    # Add rudders
    Rudder_Tube_Length = 41
    rudder_tube_l = designer.add_tube(size="0394",
                                      length=Rudder_Tube_Length,
                                      name="rudder_tube_l",
                                      mount_base_inst=rear_hub_l,
                                      mount_base_conn="Center_Connector")
    rudder_tube_r = designer.add_tube(size="0394",
                                      length=Rudder_Tube_Length,
                                      name="rudder_tube_r",
                                      mount_base_inst=rear_hub_r,
                                      mount_base_conn="Center_Connector")
    rudder_span = 140
    rudder_chord = 100
    designer.add_wing_uav(direction="Vertical",
                          chord=rudder_chord,
                          span=rudder_span,
                          thickness=wing_thickness,
                          naca=NACA_profile,
                          tube_offset=90,
                          tube_rotation=180,
                          channel=10,
                          name="left_rudder",
                          tube_inst=rudder_tube_l,
                          tube_conn="EndConnection")
    designer.add_wing_uav(direction="Vertical",
                          chord=rudder_chord,
                          span=rudder_span,
                          thickness=wing_thickness,
                          naca=NACA_profile,
                          tube_offset=50,
                          channel=9,
                          name="right_rudder",
                          tube_inst=rudder_tube_r,
                          tube_conn="EndConnection")

    designer.close_design(corpus="uav", orient_z_angle=90)


def create_test_quad_cargo():
    """
    Recreating TestQuad_Cargo design (does not include uam_direct2cad workflow at this time, 
    it only creates the graph design). This does include a cargo with weight of 0.5.
    """
    designer = Designer()
    designer.create_design("TestQuadCargoSensors")
    fuselage = designer.add_fuselage_uav(name="capsule_fuselage",
                                         floor_height=20,
                                         fuse_width=190,
                                         fuse_height=125,
                                         fuse_cyl_length=270,
                                         bottom_connector_rotation=45)
    cargo, cargo_case = designer.add_cargo(weight=0.5,
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
    # Add batteries
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

    # Add sensors
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

    # Add 4 propeller/motors
    for x in range(4):
        print("X={}".format(str(x)))
        tube_size = "0394"
        arm_name = "arm_" + str(x + 1)
        arm_length = 400
        hub_conn_name = "Side_Connector_" + str(x + 1)
        flange_name = "flange_" + str(x + 1)
        leg_name = "leg_" + str(x + 1)
        leg_length = 170
        prefix = "mp_" + str(x + 1)
        channel = x + 1
        if (x % 2) == 0:
            direction = 1
            spin = 1
        else:
            direction = -1
            spin = -1
        arm_inst = designer.add_tube(size=tube_size,
                                     length=arm_length,
                                     name=arm_name,
                                     mount_base_inst=hub_main,
                                     mount_base_conn=hub_conn_name)
        flange_inst = designer.add_flange(size=tube_size,
                                          name=flange_name,
                                          mount_side_inst=arm_inst,
                                          mount_side_conn="EndConnection")
        designer.add_tube(size=tube_size,
                          length=leg_length,
                          name=leg_name,
                          mount_base_inst=flange_inst,
                          mount_base_conn="BottomConnector")
        designer.add_motor_propeller(motor_model="t_motor_AT4130KV300",
                                     prop_model="apc_propellers_17x6",
                                     prop_type=spin,
                                     direction=direction,
                                     control_channel=channel,
                                     name_prefix=prefix,
                                     mount_inst=flange_inst,
                                     mount_conn="TopConnector",
                                     controller_inst=battery_control)

    designer.close_design(corpus="uav", orient_z_angle=45)


def create_super_quad():
    """
    Recreating SuperQuad design (does not include uam_direct2cad workflow at this time, 
    it only creates the graph design). This does include a cargo with weight of 0.5.
    """
    designer = Designer()
    designer.create_design("SuperQuadVU")
    fuselage = designer.add_fuselage_uav(name="capsule_fuselage",
                                         floor_height=20,
                                         fuse_width=250,
                                         fuse_height=220,
                                         fuse_cyl_length=505,
                                         bottom_connector_rotation=45)
    cargo, cargo_case = designer.add_cargo(weight=0.5,
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
    # Add batteries
    battery_control = designer.add_battery_controller(name="BatteryController")
    designer.add_battery_uav(model="TattuPlus25C22000mAh12S1PAGRI",
                             name="Battery_1",
                             fuse_conn_num=1,
                             mount_length=120,
                             mount_width=0,
                             controller_inst=battery_control)

    designer.add_battery_uav(model="TattuPlus25C22000mAh12S1PAGRI",
                             name="Battery_2",
                             fuse_conn_num=2,
                             mount_length=-120,
                             mount_width=0,
                             controller_inst=battery_control)

    # Add sensors
    designer.add_sensor(sensor_model="RpmTemp",
                        name="RpmTemp",
                        mount_conn_num=3,
                        rotation=90,
                        mount_length=292,
                        mount_width=0)
    designer.add_sensor(sensor_model="Current",
                        name="Current",
                        mount_conn_num=4,
                        rotation=90,
                        mount_length=-265,
                        mount_width=-45)
    designer.add_sensor(sensor_model="Autopilot",
                        name="Autopilot",
                        mount_conn_num=5,
                        rotation=90,
                        mount_length=260,
                        mount_width=5)
    designer.add_sensor(sensor_model="Voltage",
                        name="Voltage",
                        mount_conn_num=6,
                        rotation=90,
                        mount_length=-264,
                        mount_width=44)
    designer.add_sensor(sensor_model="GPS",
                        name="GPS",
                        mount_conn_num=7,
                        mount_length=-274,
                        mount_width=0)
    designer.add_sensor(sensor_model="Variometer",
                        name="Variometer",
                        mount_conn_num=8,
                        rotation=90,
                        mount_length=260,
                        mount_width=-50)

    # Add 4 propeller/motors
    for x in range(4):
        print("X={}".format(str(x)))
        tube_size = "0394"
        arm_name = "arm_" + str(x + 1)
        arm_length = 520
        hub_conn_name = "Side_Connector_" + str(x + 1)
        flange_name = "flange_" + str(x + 1)
        leg_name = "leg_" + str(x + 1)
        leg_length = 170
        prefix = "mp_" + str(x + 1)
        channel = x + 1
        if (x == 1) or (x == 4):
            direction = -1
            spin = -1
        else:
            direction = 1
            spin = 1
        arm_inst = designer.add_tube(size=tube_size,
                                     length=arm_length,
                                     name=arm_name,
                                     mount_base_inst=hub_main,
                                     mount_base_conn=hub_conn_name)
        flange_inst = designer.add_flange(size=tube_size,
                                          name=flange_name,
                                          mount_side_inst=arm_inst,
                                          mount_side_conn="EndConnection")
        designer.add_tube(size=tube_size,
                          length=leg_length,
                          name=leg_name,
                          mount_base_inst=flange_inst,
                          mount_base_conn="BottomConnector")
        designer.add_motor_propeller(motor_model="kde_direct_KDE700XF_455_G3",
                                     prop_model="apc_propellers_20x10",
                                     prop_type=spin,
                                     direction=direction,
                                     control_channel=channel,
                                     name_prefix=prefix,
                                     mount_inst=flange_inst,
                                     mount_conn="TopConnector",
                                     controller_inst=battery_control)

    designer.close_design(corpus="uav", orient_z_angle=45)


def create_pick_axe():
    """
    Recreating PickAxe design (does not include uam_direct2cad workflow at this time, 
    it only creates the graph design).
    """
    designer = Designer()
    designer.create_design("PickAxeVU")
    fuselage = designer.add_fuselage_uav(name="fuselage",
                                         floor_height=20,
                                         fuse_width=300,
                                         fuse_height=105,
                                         fuse_cyl_length=140,
                                         bottom_connector_rotation=90)
    cargo, cargo_case = designer.add_cargo(weight=0.5,
                                           name="cargo")

    # Require main_hub for connection to Orient
    # Create hub connection lists (size of num_connections max)
    # Not all connections are needed
    hub_main = designer.add_hub(name="main_hub",
                                num_connects=3,
                                connector_horizonal_angle=90,
                                connects=["Top_Connector", "Bottom_Connector"],
                                mount_inst=[fuselage, cargo_case],
                                mount_conn=["BottomConnector",
                                            "Case2HubConnector"],
                                orient_base=True)
    # Add batteries
    battery_control = designer.add_battery_controller(name="BatteryController")
    designer.add_battery_uav(model="TurnigyGraphene6000mAh6S75C",
                             name="Battery_1",
                             fuse_conn_num=2,
                             mount_length=0,
                             mount_width=-70,
                             controller_inst=battery_control)

    designer.add_battery_uav(model="TurnigyGraphene6000mAh6S75C",
                             name="Battery_2",
                             fuse_conn_num=1,
                             mount_length=0,
                             mount_width=70,
                             controller_inst=battery_control)

    # Add sensors
    designer.add_sensor(sensor_model="RpmTemp",
                        name="RpmTemp",
                        mount_conn_num=3,
                        mount_length=-20,
                        mount_width=33)
    designer.add_sensor(sensor_model="Current",
                        name="Current",
                        mount_conn_num=4,
                        mount_length=-20,
                        mount_width=-30)
    designer.add_sensor(sensor_model="Autopilot",
                        name="Autopilot",
                        mount_conn_num=5,
                        mount_length=50,
                        mount_width=0)
    designer.add_sensor(sensor_model="Voltage",
                        name="Voltage",
                        mount_conn_num=6,
                        mount_length=-20,
                        mount_width=11)
    designer.add_sensor(sensor_model="GPS",
                        name="GPS",
                        mount_conn_num=7,
                        mount_length=-80,
                        mount_width=0)
    designer.add_sensor(sensor_model="Variometer",
                        name="Variometer",
                        mount_conn_num=8,
                        mount_length=-20,
                        mount_width=-11)

    # Create front propellers section
    # Start at main hub, connect tubes on sides to side hubs,
    # then front flange and rail attach to propellers/motors
    mid_tube_l = designer.add_tube(size="0394",
                                   length=140,
                                   end_rotation=180,
                                   name="mid_tube_l",
                                   mount_base_inst=hub_main,
                                   mount_base_conn="Side_Connector_3")
    mid_tube_r = designer.add_tube(size="0394",
                                   length=140,
                                   name="mid_tube_r",
                                   mount_base_inst=hub_main,
                                   mount_base_conn="Side_Connector_1")
    side_hub_l = designer.add_hub(name="side_hub_l",
                                  num_connects=3,
                                  connector_horizonal_angle=90,
                                  connects=["Side_Connector_2"],
                                  mount_inst=[mid_tube_l],
                                  mount_conn=["EndConnection"])
    side_hub_r = designer.add_hub(name="side_hub_r",
                                  num_connects=3,
                                  connector_horizonal_angle=90,
                                  connects=["Side_Connector_2"],
                                  mount_inst=[mid_tube_r],
                                  mount_conn=["EndConnection"])
    front_rail_l = designer.add_tube(size="0394",
                                     length=135,
                                     end_rotation=270,
                                     name="front_rail_l",
                                     mount_base_inst=side_hub_l,
                                     mount_base_conn="Side_Connector_3")
    front_rail_r = designer.add_tube(size="0394",
                                     length=135,
                                     end_rotation=90,
                                     name="front_rail_r",
                                     mount_base_inst=side_hub_r,
                                     mount_base_conn="Side_Connector_3")
    front_hub_l = designer.add_hub(name="front_hub_l",
                                   num_connects=4,
                                   connector_horizonal_angle=90,
                                   connects=["Side_Connector_1"],
                                   mount_inst=[front_rail_l],
                                   mount_conn=["EndConnection"])
    front_hub_r = designer.add_hub(name="front_hub_r",
                                   num_connects=4,
                                   connector_horizonal_angle=90,
                                   connects=["Side_Connector_1"],
                                   mount_inst=[front_rail_r],
                                   mount_conn=["EndConnection"])
    front_railDwn_l = designer.add_tube(size="0394",
                                        length=90,
                                        name="front_railDwn_l",
                                        mount_base_inst=front_hub_l,
                                        mount_base_conn="Side_Connector_2")
    front_railDwn_r = designer.add_tube(size="0394",
                                        length=90,
                                        name="front_railDwn_r",
                                        mount_base_inst=front_hub_r,
                                        mount_base_conn="Side_Connector_2")
    front_hubLower_l = designer.add_hub(name="front_hubLower_l",
                                        num_connects=2,
                                        connector_horizonal_angle=270,
                                        connects=["Side_Connector_1"],
                                        mount_inst=[front_railDwn_l],
                                        mount_conn=["EndConnection"])
    front_hubLower_r = designer.add_hub(name="front_hubLower_r",
                                        num_connects=2,
                                        connector_horizonal_angle=270,
                                        connects=["Side_Connector_1"],
                                        mount_inst=[front_railDwn_r],
                                        mount_conn=["EndConnection"])
    front_railLower_l = designer.add_tube(size="0394",
                                          length=90,
                                          name="front_railLower_l",
                                          mount_base_inst=front_hubLower_l,
                                          mount_base_conn="Side_Connector_2")
    front_railLower_r = designer.add_tube(size="0394",
                                          length=90,
                                          name="front_railLower_r",
                                          mount_base_inst=front_hubLower_r,
                                          mount_base_conn="Side_Connector_2")
    front_flange_l = designer.add_flange(size="0394",
                                         name="front_flange_l",
                                         mount_bottom_inst=front_railLower_l,
                                         mount_bottom_conn="EndConnection"
                                         )
    front_flange_r = designer.add_flange(size="0394",
                                         bottom_angle=90,
                                         name="front_flange_r",
                                         mount_bottom_inst=front_railLower_r,
                                         mount_bottom_conn="EndConnection"
                                         )
    designer.add_motor_propeller(motor_model="t_motor_AntigravityMN4006KV380",
                                 prop_model="apc_propellers_12x3_8SF",
                                 prop_type=-1,
                                 direction=-1,
                                 control_channel=1,
                                 name_prefix="front_l",
                                 mount_inst=front_flange_l,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    designer.add_motor_propeller(motor_model="t_motor_AntigravityMN4006KV380",
                                 prop_model="apc_propellers_12x3_8SF",
                                 prop_type=1,
                                 direction=1,
                                 control_channel=2,
                                 name_prefix="front_r",
                                 mount_inst=front_flange_r,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    # Add front wings
    Front_Wing_Tube_Length = 52
    front_wing_tube_l = designer.add_tube(size="0394",
                                          length=Front_Wing_Tube_Length,
                                          name="front_wing_tube_l",
                                          mount_base_inst=front_flange_l,
                                          mount_base_conn="SideConnector")
    front_wing_tube_r = designer.add_tube(size="0394",
                                          length=Front_Wing_Tube_Length,
                                          name="front_wing_tube_r",
                                          mount_base_inst=front_flange_r,
                                          mount_base_conn="SideConnector")
    NACA_profile = "0012"
    front_wing_span = 450
    front_wing_chord = 150
    wing_thickness = 12
    front_tube_rotation = 180
    front_wing_load = 30
    # Note: the autograph for the seed design indicates a tube_rotation of 180 for left wing, 90 looks more correct (MM)
    designer.add_wing_uav(direction="Vertical",
                          chord=front_wing_chord,
                          span=front_wing_span,
                          thickness=wing_thickness,
                          load=front_wing_load,
                          naca=NACA_profile,
                          tube_offset=289.68,
                          tube_rotation=front_tube_rotation,
                          channel=5,
                          name="front_left_wing",
                          tube_inst=front_wing_tube_l,
                          tube_conn="EndConnection")
    designer.add_wing_uav(direction="Vertical",
                          chord=front_wing_chord,
                          span=front_wing_span,
                          thickness=wing_thickness,
                          load=front_wing_load,
                          naca=NACA_profile,
                          tube_offset=160.32,
                          tube_rotation=front_tube_rotation,
                          channel=6,
                          name="front_right_wing",
                          tube_inst=front_wing_tube_r,
                          tube_conn="EndConnection")

    # Add rear wings
    Rear_Rail_Length = 220
    rear_rail_l = designer.add_tube(size="0394",
                                    length=Rear_Rail_Length,
                                    end_rotation=90,
                                    name="rear_rail_l",
                                    mount_base_inst=side_hub_l,
                                    mount_base_conn="Side_Connector_1")
    rear_rail_r = designer.add_tube(size="0394",
                                    length=Rear_Rail_Length,
                                    end_rotation=90,
                                    name="rear_rail_r",
                                    mount_base_inst=side_hub_r,
                                    mount_base_conn="Side_Connector_1")
    rear_hub_l = designer.add_hub(name="rear_hub_l",
                                  num_connects=3,
                                  connector_horizonal_angle=90,
                                  connects=["Side_Connector_1"],
                                  mount_inst=[rear_rail_l],
                                  mount_conn=["EndConnection"])
    rear_hub_r = designer.add_hub(name="rear_hub_r",
                                  num_connects=3,
                                  connector_horizonal_angle=90,
                                  connects=["Side_Connector_3"],
                                  mount_inst=[rear_rail_r],
                                  mount_conn=["EndConnection"])
    bottom_leg_l = designer.add_tube(size="0394",
                                     length=150,
                                     name="bottom_leg_l",
                                     mount_base_inst=rear_hub_l,
                                     mount_base_conn="Side_Connector_3")
    bottom_leg_r = designer.add_tube(size="0394",
                                     length=150,
                                     name="bottom_leg_r",
                                     mount_base_inst=rear_hub_r,
                                     mount_base_conn="Side_Connector_1")
    vertical_l = designer.add_tube(size="0394",
                                   length=150,
                                   end_rotation=90,
                                   offset_1=90,
                                   name="vertical_l",
                                   mount_base_inst=rear_hub_l,
                                   mount_base_conn="Side_Connector_2")
    vertical_r = designer.add_tube(size="0394",
                                   length=150,
                                   end_rotation=270,
                                   offset_1=90,
                                   name="vertical_r",
                                   mount_base_inst=rear_hub_r,
                                   mount_base_conn="Side_Connector_2")
    rear_wing_span = 609
    rear_wing_chord = 180
    rear_wing_load = 30
    designer.add_wing_uav(direction="Vertical",
                          chord=rear_wing_chord,
                          span=rear_wing_span,
                          thickness=wing_thickness,
                          load=rear_wing_load,
                          naca=NACA_profile,
                          tube_offset=448.68,
                          tube_rotation=270,
                          channel=8,
                          name="rear_left_wing",
                          tube_inst=vertical_l,
                          tube_conn="OffsetConnection1")
    designer.add_wing_uav(direction="Vertical",
                          chord=rear_wing_chord,
                          span=rear_wing_span,
                          thickness=wing_thickness,
                          load=rear_wing_load,
                          naca=NACA_profile,
                          tube_offset=160.32,
                          tube_rotation=90,
                          channel=7,
                          name="rear_right_wing",
                          tube_inst=vertical_r,
                          tube_conn="OffsetConnection1")
    rear_flange_l = designer.add_flange(size="0394",
                                        name="rear_flange_l",
                                        mount_side_inst=vertical_l,
                                        mount_side_conn="EndConnection"
                                        )
    rear_flange_r = designer.add_flange(size="0394",
                                        name="rear_flange_r",
                                        mount_side_inst=vertical_r,
                                        mount_side_conn="EndConnection"
                                        )
    designer.add_motor_propeller(motor_model="t_motor_AntigravityMN4006KV380",
                                 prop_model="apc_propellers_12x3_8SF",
                                 prop_type=-1,
                                 direction=-1,
                                 control_channel=3,
                                 name_prefix="rear_l",
                                 mount_inst=rear_flange_l,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    designer.add_motor_propeller(motor_model="t_motor_AntigravityMN4006KV380",
                                 prop_model="apc_propellers_12x3_8SF",
                                 prop_type=1,
                                 direction=1,
                                 control_channel=4,
                                 name_prefix="rear_r",
                                 mount_inst=rear_flange_r,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    Top_Leg_Tube_Length = 150.1524
    top_leg_l = designer.add_tube(size="0394",
                                  length=Top_Leg_Tube_Length,
                                  name="top_leg_l",
                                  mount_base_inst=rear_flange_l,
                                  mount_base_conn="BottomConnector")
    top_leg_r = designer.add_tube(size="0394",
                                  length=Top_Leg_Tube_Length,
                                  name="top_leg_r",
                                  mount_base_inst=rear_flange_r,
                                  mount_base_conn="BottomConnector")

    # Add rudders
    Rudder_Tube_Length = 41
    rudder_tube_l = designer.add_tube(size="0394",
                                      length=Rudder_Tube_Length,
                                      name="rudder_tube_l",
                                      mount_base_inst=rear_hub_l,
                                      mount_base_conn="Center_Connector")
    rudder_tube_r = designer.add_tube(size="0394",
                                      length=Rudder_Tube_Length,
                                      name="rudder_tube_r",
                                      mount_base_inst=rear_hub_r,
                                      mount_base_conn="Center_Connector")
    rudder_span = 140
    rudder_chord = 100
    rudder_load = 20
    designer.add_wing_uav(direction="Vertical",
                          chord=rudder_chord,
                          span=rudder_span,
                          thickness=wing_thickness,
                          load=rudder_load,
                          naca=NACA_profile,
                          tube_offset=90,
                          tube_rotation=180,
                          channel=10,
                          name="left_rudder",
                          tube_inst=rudder_tube_l,
                          tube_conn="EndConnection")
    designer.add_wing_uav(direction="Vertical",
                          chord=rudder_chord,
                          span=rudder_span,
                          thickness=wing_thickness,
                          load=rudder_load,
                          naca=NACA_profile,
                          tube_offset=50,
                          channel=9,
                          name="right_rudder",
                          tube_inst=rudder_tube_r,
                          tube_conn="EndConnection")

    designer.close_design(corpus="uav", orient_z_angle=90)


def create_inline_uav():
    """
    This design will place the cargo inline behind the fuselage, but under the wings

    Elements of design:
    * Fuselage (bottom connector only)
    * Tube from fuselage to hub
    """
    designer = Designer()
    designer.create_design("InlineUAV")
    tube_size = "0281"
    tube_diameter = 7.1474
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
                                diameter=tube_diameter,
                                connector_horizonal_angle=0,
                                connector_vertical_angle=180,
                                connects=["Bottom_Connector"],
                                mount_inst=[fuselage],
                                mount_conn=["BottomConnector"])

    # Add batteries
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

    # Add sensors
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

    # Tube between main hub and center structure to move fuselage vertically
    fuse_vert_length = 20
    fuse_hub_tube = designer.add_tube(size=tube_size,
                                      length=fuse_vert_length,
                                      end_rotation=180,
                                      name="fuse_hub_tube",
                                      mount_base_inst=hub_main,
                                      mount_base_conn="Top_Connector")
    center_hub = designer.add_hub(name="center_hub",
                                  num_connects=4,
                                  diameter=tube_diameter,
                                  connector_horizonal_angle=90,
                                  connects=["Bottom_Connector"],
                                  mount_inst=[fuse_hub_tube],
                                  mount_conn=["EndConnection"],
                                  orient_base=True)

    # Cargo section - tube from 4 way hub (1) to 2 way hub
    cargo_tube_length = 305
    center_cargo_tube = designer.add_tube(size=tube_size,
                                          length=cargo_tube_length,
                                          end_rotation=180,
                                          name="center_cargo_tube",
                                          mount_base_inst=center_hub,
                                          mount_base_conn="Side_Connector_1")
    cargo_hub = designer.add_hub(name="cargo_hub",
                                 num_connects=4,
                                 diameter=tube_diameter,
                                 connector_horizonal_angle=0,
                                 connects=["Side_Connector_2",
                                           "Top_Connector"],
                                 mount_inst=[center_cargo_tube, cargo_case],
                                 mount_conn=["EndConnection", "Case2HubConnector"])

    # Wings section - 2 horizontal tubes from 4 way hub (2 & 4) to 2 way hubs
    #                 2 vertical tubes to attach to vertical wings
    NACA_profile = "0012"
    wing_span = 550
    wing_chord = 150
    wing_thickness = 12
    wing_load = 30
    tube_offset = wing_span / 2
    wing_hort_tube_length = wing_span - tube_offset - 14.93 - (tube_diameter * 1.5) / 2
    #wing_hort_tube_length = wing_span - tube_offset - 16.51 - (tube_diameter * 1.5) / 2
    wing_hort_tube_l = designer.add_tube(size=tube_size,
                                         length=wing_hort_tube_length,
                                         end_rotation=180,
                                         name="wing_hort_tube_l",
                                         mount_base_inst=center_hub,
                                         mount_base_conn="Side_Connector_2")
    wing_hort_tube_r = designer.add_tube(size=tube_size,
                                         length=wing_hort_tube_length,
                                         end_rotation=180,
                                         name="wing_hort_tube_r",
                                         mount_base_inst=center_hub,
                                         mount_base_conn="Side_Connector_4")
    wing_hub_l = designer.add_hub(name="wing_hub_l",
                                  num_connects=2,
                                  diameter=tube_diameter,
                                  connector_horizonal_angle=0,
                                  connector_vertical_angle=180,
                                  connects=["Side_Connector_2"],
                                  mount_inst=[wing_hort_tube_l],
                                  mount_conn=["EndConnection"])
    wing_hub_r = designer.add_hub(name="wing_hub_r",
                                  num_connects=2,
                                  diameter=tube_diameter,
                                  connector_horizonal_angle=0,
                                  connector_vertical_angle=180,
                                  connects=["Side_Connector_1"],
                                  mount_inst=[wing_hort_tube_r],
                                  mount_conn=["EndConnection"])
    wing_vert_tube_length = 50
    wing_vert_tube_l = designer.add_tube(size=tube_size,
                                         length=wing_vert_tube_length,
                                         end_rotation=180,
                                         name="wing_vert_tube_l",
                                         mount_base_inst=wing_hub_l,
                                         mount_base_conn="Top_Connector")
    wing_vert_tube_r = designer.add_tube(size=tube_size,
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
                          tube_diameter=tube_diameter,
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
                          tube_diameter=tube_diameter,
                          tube_offset=tube_offset,
                          tube_rotation=270,
                          channel=2,
                          name="right_wing",
                          tube_inst=wing_vert_tube_r,
                          tube_conn="EndConnection")

    # Prop/motor section - tube from 4 way hub (3) to 3 way hub
    #                      2 tubes horizontally to 3 way hubs
    #                      2 vertical tubes out from 3 hubs (on each side) to flanges
    #                      4 prop/motors attached to flanges
    prop_forward_length = 250
    center_tube_prop = designer.add_tube(size=tube_size,
                                         length=prop_forward_length,
                                         end_rotation=180,
                                         name="center_tube_prop",
                                         mount_base_inst=center_hub,
                                         mount_base_conn="Side_Connector_3")
    front_hub = designer.add_hub(name="front_hub",
                                 num_connects=3,
                                 diameter=tube_diameter,
                                 connector_horizonal_angle=90,
                                 connects=["Side_Connector_2"],
                                 mount_inst=[center_tube_prop],
                                 mount_conn=["EndConnection"])
    prop_hort_spread_length = 160
    prop_hort_tube_l = designer.add_tube(size=tube_size,
                                         length=prop_hort_spread_length,
                                         end_rotation=180,
                                         name="prop_hort_tube_l",
                                         mount_base_inst=front_hub,
                                         mount_base_conn="Side_Connector_1")
    prop_hort_tube_r = designer.add_tube(size=tube_size,
                                         length=prop_hort_spread_length,
                                         end_rotation=180,
                                         name="prop_hort_tube_r",
                                         mount_base_inst=front_hub,
                                         mount_base_conn="Side_Connector_3")
    prop_hub_l = designer.add_hub(name="prop_hub_l",
                                  num_connects=2,
                                  diameter=tube_diameter,
                                  connector_horizonal_angle=180,
                                  connector_vertical_angle=0,
                                  connects=["Bottom_Connector"],
                                  mount_inst=[prop_hort_tube_l],
                                  mount_conn=["EndConnection"])
    prop_hub_r = designer.add_hub(name="prop_hub_r",
                                  num_connects=2,
                                  diameter=tube_diameter,
                                  connector_horizonal_angle=180,
                                  connector_vertical_angle=0,
                                  connects=["Top_Connector"],
                                  mount_inst=[prop_hort_tube_r],
                                  mount_conn=["EndConnection"])

    prop_vert_spread_length = 210
    top_prop_tube_l = designer.add_tube(size=tube_size,
                                        length=prop_vert_spread_length,
                                        end_rotation=90,
                                        name="top_prop_tube_l",
                                        mount_base_inst=prop_hub_l,
                                        mount_base_conn="Side_Connector_1")
    top_prop_tube_r = designer.add_tube(size=tube_size,
                                        length=prop_vert_spread_length,
                                        end_rotation=90,
                                        name="top_prop_tube_r",
                                        mount_base_inst=prop_hub_r,
                                        mount_base_conn="Side_Connector_1")
    top_prop_flange_l = designer.add_flange(size=tube_size,
                                            name="top_prop_flange_l",
                                            mount_side_inst=top_prop_tube_l,
                                            mount_side_conn="EndConnection"
                                            )
    designer.add_motor_propeller(motor_model="t_motor_AntigravityMN4006KV380",
                                 prop_model="apc_propellers_12x3_8SF",
                                 prop_type=1,
                                 direction=1,
                                 control_channel=3,
                                 name_prefix="top_l",
                                 mount_inst=top_prop_flange_l,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    top_prop_flange_r = designer.add_flange(size=tube_size,
                                            name="top_prop_flange_r",
                                            mount_side_inst=top_prop_tube_r,
                                            mount_side_conn="EndConnection"
                                            )
    designer.add_motor_propeller(motor_model="t_motor_AntigravityMN4006KV380",
                                 prop_model="apc_propellers_12x3_8SF",
                                 prop_type=-1,
                                 direction=-1,
                                 control_channel=4,
                                 name_prefix="top_r",
                                 mount_inst=top_prop_flange_r,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    bottom_prop_tube_l = designer.add_tube(size=tube_size,
                                           length=prop_vert_spread_length,
                                           end_rotation=270,
                                           name="bottom_prop_tube_l",
                                           mount_base_inst=prop_hub_l,
                                           mount_base_conn="Side_Connector_2")
    bottom_prop_tube_r = designer.add_tube(size=tube_size,
                                           length=prop_vert_spread_length,
                                           end_rotation=270,
                                           name="bottom_prop_tube_r",
                                           mount_base_inst=prop_hub_r,
                                           mount_base_conn="Side_Connector_2")
    bottom_prop_flange_l = designer.add_flange(size=tube_size,
                                               name="bottom_prop_flange_l",
                                               mount_side_inst=bottom_prop_tube_l,
                                               mount_side_conn="EndConnection"
                                               )
    designer.add_motor_propeller(motor_model="t_motor_AntigravityMN4006KV380",
                                 prop_model="apc_propellers_12x3_8SF",
                                 prop_type=-1,
                                 direction=-1,
                                 control_channel=5,
                                 name_prefix="bottom_l",
                                 mount_inst=bottom_prop_flange_l,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    bottom_prop_flange_r = designer.add_flange(size=tube_size,
                                               name="bottom_prop_flange_r",
                                               mount_side_inst=bottom_prop_tube_r,
                                               mount_side_conn="EndConnection"
                                               )
    designer.add_motor_propeller(motor_model="t_motor_AntigravityMN4006KV380",
                                 prop_model="apc_propellers_12x3_8SF",
                                 prop_type=1,
                                 direction=1,
                                 control_channel=6,
                                 name_prefix="bottom_r",
                                 mount_inst=bottom_prop_flange_r,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
 
    designer.close_design(corpus="uav", orient_z_angle=180)


def create_uno_inline_uav(tail_wing = False):
    """
    This design will place the cargo inline behind the fuselage, but under a single wing.
    Optionally a tail wing can be added.

    Elements of design:
    * Fuselage (bottom connector only)
    * Tube from fuselage to hub
    """
    designer = Designer()
    designer.create_design("UnoInlineUAV")
    tube_size = "0281"
    tube_diameter = 7.1474
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
                                diameter=tube_diameter,
                                connector_horizonal_angle=0,
                                connector_vertical_angle=180,
                                connects=["Bottom_Connector"],
                                mount_inst=[fuselage],
                                mount_conn=["BottomConnector"])

    # Add batteries
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

    # Add sensors
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

    # Tube between main hub and center structure to move fuselage vertically
    fuse_vert_length = 20
    fuse_hub_tube = designer.add_tube(size=tube_size,
                                      length=fuse_vert_length,
                                      end_rotation=0,
                                      name="fuse_hub_tube",
                                      mount_base_inst=hub_main,
                                      mount_base_conn="Top_Connector")
    center_hub = designer.add_hub(name="center_hub",
                                  num_connects=2,
                                  diameter=tube_diameter,
                                  connector_horizonal_angle=180,
                                  connector_vertical_angle=180,
                                  connects=["Bottom_Connector"],
                                  mount_inst=[fuse_hub_tube],
                                  mount_conn=["EndConnection"],
                                  orient_base=True)

    # Cargo section - tube from 4 way hub (1) to 2 way hub
    cargo_tube_length = 305
    center_cargo_tube = designer.add_tube(size=tube_size,
                                          length=cargo_tube_length,
                                          end_rotation=180,
                                          name="center_cargo_tube",
                                          mount_base_inst=center_hub,
                                          mount_base_conn="Side_Connector_2")
    cargo_hub = designer.add_hub(name="cargo_hub",
                                 num_connects=4,
                                 diameter=tube_diameter,
                                 connector_horizonal_angle=0,
                                 connects=["Side_Connector_2",
                                           "Bottom_Connector"],
                                 mount_inst=[center_cargo_tube, cargo_case],
                                 mount_conn=["EndConnection", "Case2HubConnector"])

    # Wings section - 2 horizontal tubes from 4 way hub (2 & 4) to 2 way hubs
    #                 2 vertical tubes to attach to vertical wings
    NACA_profile = "0012"
    wing_span = 1200
    wing_chord = 150
    wing_thickness = 12
    wing_load = 30
    tube_offset = wing_span / 2
    front_wing_tube_length = 50
    front_wing_tube = designer.add_tube(size=tube_size,
                                         length=front_wing_tube_length,
                                         end_rotation=180,
                                         name="front_wing_tube",
                                         mount_base_inst=center_hub,
                                         mount_base_conn="Top_Connector")
    front_wing = designer.add_wing_uav(direction="Vertical",
                          chord=wing_chord,
                          span=wing_span,
                          thickness=wing_thickness,
                          load=wing_load,
                          naca=NACA_profile,
                          tube_diameter=tube_diameter,
                          tube_offset=tube_offset,
                          tube_rotation=180,
                          channel=1,
                          name="front_wing",
                          tube_inst=front_wing_tube,
                          tube_conn="EndConnection")
    designer.set_named_parameter([front_wing], "WingChord", "CHORD_1", wing_chord)
    designer.set_named_parameter([front_wing], "WingChord", "CHORD_2", wing_chord, param_exist=True)

    # Prop/motor section - tube from 4 way hub (3) to 3 way hub
    #                      2 tubes horizontally to 3 way hubs
    #                      2 vertical tubes out from 3 hubs (on each side) to flanges
    #                      4 prop/motors attached to flanges
    prop_forward_length = 250
    center_tube_prop = designer.add_tube(size=tube_size,
                                         length=prop_forward_length,
                                         end_rotation=0,
                                         name="center_tube_prop",
                                         mount_base_inst=center_hub,
                                         mount_base_conn="Side_Connector_1")
    front_hub = designer.add_hub(name="front_hub",
                                 num_connects=3,
                                 diameter=tube_diameter,
                                 connector_horizonal_angle=90,
                                 connects=["Side_Connector_2"],
                                 mount_inst=[center_tube_prop],
                                 mount_conn=["EndConnection"])

    prop_hort_spread_length = 140
    prop_hort_tube_l = designer.add_tube(size=tube_size,
                                         length=prop_hort_spread_length,
                                         end_rotation=180,
                                         name="prop_hort_tube_l",
                                         mount_base_inst=front_hub,
                                         mount_base_conn="Side_Connector_1")
    prop_hort_tube_r = designer.add_tube(size=tube_size,
                                         length=prop_hort_spread_length,
                                         end_rotation=180,
                                         name="prop_hort_tube_r",
                                         mount_base_inst=front_hub,
                                         mount_base_conn="Side_Connector_3")
    prop_hub_l = designer.add_hub(name="prop_hub_l",
                                  num_connects=2,
                                  diameter=tube_diameter,
                                  connector_horizonal_angle=180,
                                  connector_vertical_angle=0,
                                  connects=["Bottom_Connector"],
                                  mount_inst=[prop_hort_tube_l],
                                  mount_conn=["EndConnection"])
    prop_hub_r = designer.add_hub(name="prop_hub_r",
                                  num_connects=2,
                                  diameter=tube_diameter,
                                  connector_horizonal_angle=180,
                                  connector_vertical_angle=0,
                                  connects=["Top_Connector"],
                                  mount_inst=[prop_hort_tube_r],
                                  mount_conn=["EndConnection"])
    designer.set_named_parameter([prop_hub_l, prop_hub_r], "HortSpread", "Length", prop_hort_spread_length)

    prop_vert_spread_length_t = 100
    prop_vert_spread_length_b = 210
    top_prop_tube_l = designer.add_tube(size=tube_size,
                                        length=prop_vert_spread_length_t,
                                        end_rotation=90,
                                        name="top_prop_tube_l",
                                        mount_base_inst=prop_hub_l,
                                        mount_base_conn="Side_Connector_1")
    top_prop_tube_r = designer.add_tube(size=tube_size,
                                        length=prop_vert_spread_length_t,
                                        end_rotation=90,
                                        name="top_prop_tube_r",
                                        mount_base_inst=prop_hub_r,
                                        mount_base_conn="Side_Connector_1")
    top_prop_flange_l = designer.add_flange(size=tube_size,
                                            name="top_prop_flange_l",
                                            mount_side_inst=top_prop_tube_l,
                                            mount_side_conn="EndConnection"
                                            )
    designer.add_motor_propeller(motor_model="t_motor_AntigravityMN4006KV380",
                                 prop_model="apc_propellers_12x3_8SF",
                                 prop_type=1,
                                 direction=1,
                                 control_channel=3,
                                 name_prefix="top_l",
                                 mount_inst=top_prop_flange_l,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    top_prop_flange_r = designer.add_flange(size=tube_size,
                                            name="top_prop_flange_r",
                                            mount_side_inst=top_prop_tube_r,
                                            mount_side_conn="EndConnection"
                                            )
    designer.add_motor_propeller(motor_model="t_motor_AntigravityMN4006KV380",
                                 prop_model="apc_propellers_12x3_8SF",
                                 prop_type=-1,
                                 direction=-1,
                                 control_channel=4,
                                 name_prefix="top_r",
                                 mount_inst=top_prop_flange_r,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    bottom_prop_tube_l = designer.add_tube(size=tube_size,
                                           length=prop_vert_spread_length_b,
                                           end_rotation=270,
                                           name="bottom_prop_tube_l",
                                           mount_base_inst=prop_hub_l,
                                           mount_base_conn="Side_Connector_2")
    bottom_prop_tube_r = designer.add_tube(size=tube_size,
                                           length=prop_vert_spread_length_b,
                                           end_rotation=270,
                                           name="bottom_prop_tube_r",
                                           mount_base_inst=prop_hub_r,
                                           mount_base_conn="Side_Connector_2")
    bottom_prop_flange_l = designer.add_flange(size=tube_size,
                                               name="bottom_prop_flange_l",
                                               mount_side_inst=bottom_prop_tube_l,
                                               mount_side_conn="EndConnection"
                                               )
    designer.add_motor_propeller(motor_model="t_motor_AntigravityMN4006KV380",
                                 prop_model="apc_propellers_12x3_8SF",
                                 prop_type=-1,
                                 direction=-1,
                                 control_channel=5,
                                 name_prefix="bottom_l",
                                 mount_inst=bottom_prop_flange_l,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    bottom_prop_flange_r = designer.add_flange(size=tube_size,
                                               name="bottom_prop_flange_r",
                                               mount_side_inst=bottom_prop_tube_r,
                                               mount_side_conn="EndConnection"
                                               )
    designer.add_motor_propeller(motor_model="t_motor_AntigravityMN4006KV380",
                                 prop_model="apc_propellers_12x3_8SF",
                                 prop_type=1,
                                 direction=1,
                                 control_channel=6,
                                 name_prefix="bottom_r",
                                 mount_inst=bottom_prop_flange_r,
                                 mount_conn="TopConnector",
                                 controller_inst=battery_control)
    designer.set_named_parameter([top_prop_tube_l, top_prop_tube_r], "TopVertSpread", "Length", prop_vert_spread_length_t)
    designer.set_named_parameter([bottom_prop_tube_l, bottom_prop_tube_r], "BottomVertSpread", "Length", prop_vert_spread_length_b)

    designer.close_design(corpus="uav", orient_z_angle=180)


def create_tiltie(num_batts = 1, narrow_fuse = False, tail = False):
    """
    This design will place the cargo inline behind the fuselage, but under a single wing.
    The propellers will be tiltable and controllable by a system parameter.
    """
    designer = Designer()
    tube_size = "0281"
    tube_diameter = 7.1474
    motor_type = "t_motor_AntigravityMN5008KV340"
    prop_type = "apc_propellers_13x14"
    battery_type = "Tattu25C23000mAh6S1PHV"
    
    if num_batts == 2:
        designer.create_design("Tiltie")
        fuselage = designer.add_fuselage_uav(name="fuselage",
                                            floor_height=20,
                                            fuse_width=190,
                                            fuse_height=125,
                                            fuse_cyl_length=270,
                                            bottom_connector_rotation=0)
    elif narrow_fuse and num_batts == 1:
        if tail:
            designer.create_design("TiltieTailed")
        else:
            designer.create_design("TiltieTrimmed")
        fuselage = designer.add_fuselage_uav(name="fuselage",
                                            floor_height=14,
                                            fuse_width=112,
                                            fuse_height=125,
                                            fuse_cyl_length=368,
                                            bottom_connector_rotation=0)
    elif num_batts == 1:
        designer.create_design("TiltieDyno")
        fuselage = designer.add_fuselage_uav(name="fuselage",
                                            floor_height=20,
                                            fuse_width=190,
                                            fuse_height=125,
                                            fuse_cyl_length=289,
                                            bottom_connector_rotation=0)
    cargo, cargo_case = designer.add_cargo(weight=0.5,
                                           name="cargo")

    # Require main_hub for connection to Orient
    # Create hub connection lists (size of num_connections max)
    # Not all connections are needed
    hub_main = designer.add_hub(name="main_hub",
                                num_connects=2,
                                diameter=tube_diameter,
                                connector_horizonal_angle=0,
                                connector_vertical_angle=180,
                                connects=["Bottom_Connector"],
                                mount_inst=[fuselage],
                                mount_conn=["BottomConnector"])

    # Add batteries
    battery_control = designer.add_battery_controller(name="BatteryController")
    if num_batts == 2:
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
    elif num_batts == 1:
        designer.add_battery_uav(model=battery_type,
                                name="Battery_1",
                                fuse_conn_num=1,
                                mount_length=0,
                                mount_width=0,
                                controller_inst=battery_control)

    # Add sensors
    if num_batts == 2:
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
    elif narrow_fuse and num_batts == 1:
        designer.add_sensor(sensor_model="RpmTemp",
                            name="RpmTemp",
                            mount_conn_num=3,
                            rotation=90,
                            mount_length=-180,
                            mount_width=16)
        designer.add_sensor(sensor_model="Current",
                            name="Current",
                            mount_conn_num=4,
                            rotation=90,
                            mount_length=-180,
                            mount_width=-15)
        designer.add_sensor(sensor_model="Autopilot",
                            name="Autopilot",
                            mount_conn_num=5,
                            rotation=0,
                            mount_length=147,
                            mount_width=0)
        designer.add_sensor(sensor_model="Voltage",
                            name="Voltage",
                            mount_conn_num=6,
                            rotation=90,
                            mount_length=-202,
                            mount_width=0)
        designer.add_sensor(sensor_model="GPS",
                            name="GPS",
                            mount_conn_num=7,
                            mount_length=-140,
                            mount_width=0)
        designer.add_sensor(sensor_model="Variometer",
                            name="Variometer",
                            mount_conn_num=8,
                            rotation=90,
                            mount_length=199,
                            mount_width=0)
    elif num_batts == 1:
        designer.add_sensor(sensor_model="RpmTemp",
                            name="RpmTemp",
                            mount_conn_num=3,
                            rotation=90,
                            mount_length=-172,
                            mount_width=13)
        designer.add_sensor(sensor_model="Current",
                            name="Current",
                            mount_conn_num=4,
                            rotation=90,
                            mount_length=-172,
                            mount_width=-18)
        designer.add_sensor(sensor_model="Autopilot",
                            name="Autopilot",
                            mount_conn_num=5,
                            rotation=90,
                            mount_length=125,
                            mount_width=0)
        designer.add_sensor(sensor_model="Voltage",
                            name="Voltage",
                            mount_conn_num=6,
                            rotation=90,
                            mount_length=162,
                            mount_width=18)
        designer.add_sensor(sensor_model="GPS",
                            name="GPS",
                            mount_conn_num=7,
                            mount_length=-130,
                            mount_width=0)
        designer.add_sensor(sensor_model="Variometer",
                            name="Variometer",
                            mount_conn_num=8,
                            rotation=90,
                            mount_length=162,
                            mount_width=-18)

    # Tube between main hub and center structure to move fuselage vertically
    fuse_vert_length = 20
    fuse_hub_tube = designer.add_tube(size=tube_size,
                                      length=fuse_vert_length,
                                      end_rotation=0,
                                      name="fuse_hub_tube",
                                      mount_base_inst=hub_main,
                                      mount_base_conn="Top_Connector")
    center_hub = designer.add_hub(name="center_hub",
                                  num_connects=2,
                                  diameter=tube_diameter,
                                  connector_horizonal_angle=180,
                                  connector_vertical_angle=180,
                                  connects=["Bottom_Connector"],
                                  mount_inst=[fuse_hub_tube],
                                  mount_conn=["EndConnection"],
                                  orient_base=True)

    # Cargo section - tube from 4 way hub (1) to 2 way hub
    cargo_tube_length = 305
    cargo_attach_tube_length = 5
    center_cargo_tube = designer.add_tube(size=tube_size,
                                          length=cargo_tube_length,
                                          end_rotation=180,
                                          name="center_cargo_tube",
                                          mount_base_inst=center_hub,
                                          mount_base_conn="Side_Connector_2")
    if tail:
        back_hub = designer.add_hub(name="back_hub",
                            num_connects=2,
                            diameter=tube_diameter,
                            connector_horizonal_angle=180,
                            connects=["Side_Connector_1"],
                            mount_inst=[center_cargo_tube],
                            mount_conn=["EndConnection"])
    else:
        back_hub = designer.add_hub(name="back_hub",
                                    num_connects=2,
                                    diameter=tube_diameter,
                                    connector_horizonal_angle=0,
                                    connects=["Side_Connector_1"],
                                    mount_inst=[center_cargo_tube],
                                    mount_conn=["EndConnection"])
    cargo_attach_tube = designer.add_tube(size=tube_size,
                                         length=cargo_attach_tube_length,
                                         end_rotation=180,
                                         name="cargo_attach_tube",
                                         mount_base_inst=back_hub,
                                         mount_base_conn="Bottom_Connector")
    cargo_hub = designer.add_hub(name="cargo_hub",
                                num_connects=2,
                                diameter=tube_diameter,
                                connector_horizonal_angle=0,
                                connector_vertical_angle=0,
                                connects=["Top_Connector","Bottom_Connector"],
                                mount_inst=[cargo_attach_tube,cargo_case],
                                mount_conn=["EndConnection","Case2HubConnector"])

    # Front Wing section - 2 horizontal tubes from 4 way hub (2 & 4) to 2 way hubs
    #                      2 vertical tubes to attach to vertical wings
    NACA_profile = "0012"
    wing_span = 1200
    wing_chord = 150
    wing_thickness = 12
    wing_load = 30
    tube_offset = wing_span / 2
    front_wing_tube_length = 50
    front_wing_tube = designer.add_tube(size=tube_size,
                                         length=front_wing_tube_length,
                                         end_rotation=180,
                                         name="front_wing_tube",
                                         mount_base_inst=center_hub,
                                         mount_base_conn="Top_Connector")
    front_wing = designer.add_wing_uav(direction="Vertical",
                          chord=wing_chord,
                          span=wing_span,
                          thickness=wing_thickness,
                          load=wing_load,
                          naca=NACA_profile,
                          tube_diameter=tube_diameter,
                          tube_offset=tube_offset,
                          tube_rotation=180,
                          channel=1,
                          name="front_wing",
                          tube_inst=front_wing_tube,
                          tube_conn="EndConnection")
    designer.set_named_parameter([front_wing], "WingChord", "CHORD_1", wing_chord)
    designer.set_named_parameter([front_wing], "WingChord", "CHORD_2", wing_chord, param_exist=True)

    # Add V tail
    if tail:
        tail_extension_length = 200
        tail_extension_tube = designer.add_tube(size=tube_size,
                                    length=tail_extension_length,
                                    end_rotation=0,
                                    name="tail_extension_tube",
                                    mount_base_inst=back_hub,
                                    mount_base_conn="Side_Connector_2")
        tail_hub = designer.add_hub(name="tail_hub",
                                    num_connects=2,
                                    diameter=tube_diameter,
                                    connector_horizonal_angle=0,
                                    connects=["Side_Connector_1"],
                                    mount_inst=[tail_extension_tube],
                                    mount_conn=["EndConnection"])
        tail_attach_tube_length = 25
        tail_attach_tube = designer.add_tube(size=tube_size,
                                            length=tail_attach_tube_length,
                                            end_rotation=180,
                                            name="tail_attach_tube",
                                            mount_base_inst=tail_hub,
                                            mount_base_conn="Top_Connector")
        tail_wing_hub = designer.add_hub(name="tail_wing_hub",
                                    num_connects=3,
                                    diameter=tube_diameter,
                                    connector_horizonal_angle=120,
                                    connector_vertical_angle=0,
                                    connects=["Side_Connector_1"],
                                    mount_inst=[tail_attach_tube],
                                    mount_conn=["EndConnection"])
        tail_tube_length = 50
        tail_tube_l = designer.add_tube(size=tube_size,
                                        length=tail_tube_length,
                                        end_rotation=180,
                                        name="tail_tube_l",
                                        mount_base_inst=tail_wing_hub,
                                        mount_base_conn="Side_Connector_3")
        tail_tube_r = designer.add_tube(size=tube_size,
                                        length=tail_tube_length,
                                        end_rotation=180,
                                        name="tail_tube_r",
                                        mount_base_inst=tail_wing_hub,
                                        mount_base_conn="Side_Connector_2")
        NACA_profile = "0012"
        tail_wing_span = 500
        tail_wing_chord = 150
        tail_wing_thickness = 12
        tail_wing_load = 15
        tail_tube_offset = wing_span / 2
        tail_wing_l = designer.add_wing_uav(direction="Horizontal",
                            chord=tail_wing_chord,
                            span=tail_wing_span,
                            thickness=tail_wing_thickness,
                            load=tail_wing_load,
                            naca=NACA_profile,
                            tube_diameter=tube_diameter,
                            tube_offset=tail_tube_offset,
                            tube_rotation=0,
                            channel=1,
                            name="tail_wing_l",
                            tube_inst=tail_tube_l,
                            tube_conn="EndConnection")
        tail_wing_r = designer.add_wing_uav(direction="Horizontal",
                            chord=tail_wing_chord,
                            span=tail_wing_span,
                            thickness=tail_wing_thickness,
                            load=tail_wing_load,
                            naca=NACA_profile,
                            tube_diameter=tube_diameter,
                            tube_offset=tail_tube_offset,
                            tube_rotation=0,
                            channel=1,
                            name="tail_wing_r",
                            tube_inst=tail_tube_r,
                            tube_conn="EndConnection")
        designer.set_named_parameter([tail_wing_l, tail_wing_r], "TailWingChord", "CHORD_1", wing_chord)
        designer.set_named_parameter([tail_wing_l, tail_wing_r], "TailWingChord", "CHORD_2", wing_chord, param_exist=True)
        designer.set_named_parameter([tail_wing_l, tail_wing_r], "TailSpan", "SPAN", tail_wing_span)
        designer.set_named_parameter([tail_wing_l, tail_wing_r], "TailLoad", "LOAD", tail_wing_load)
        designer.set_named_parameter([tail_tube_l, tail_tube_r], "TailExtension", "LENGTH", tail_tube_length)

    # Prop/motor section - tube from 4 way hub (3) to 3 way hub
    #                      2 tubes horizontally to 3 way hubs
    #                      2 vertical tubes out from 3 hubs (on each side) to flanges
    #                      4 prop/motors attached to flanges
    prop_forward_length = 250
    center_tube_prop = designer.add_tube(size=tube_size,
                                         length=prop_forward_length,
                                         end_rotation=0,
                                         name="center_tube_prop",
                                         mount_base_inst=center_hub,
                                         mount_base_conn="Side_Connector_1")
    front_hub = designer.add_hub(name="front_hub",
                                 num_connects=3,
                                 diameter=tube_diameter,
                                 connector_horizonal_angle=180,
                                 connects=["Center_Connector"],
                                 mount_inst=[center_tube_prop],
                                 mount_conn=["EndConnection"])
    prop_vert_spread_length_t = 50
    prop_vert_spread_length_b = 100
    top_vert_prop_tube = designer.add_tube(size=tube_size,
                                        length=prop_vert_spread_length_t,
                                        end_rotation=90,
                                        name="top_vert_prop_tube",
                                        mount_base_inst=front_hub,
                                        mount_base_conn="Side_Connector_1")
    bottom_vert_prop_tube = designer.add_tube(size=tube_size,
                                        length=prop_vert_spread_length_b,
                                        end_rotation=90,
                                        name="bottom_vert_prop_tube",
                                        mount_base_inst=front_hub,
                                        mount_base_conn="Side_Connector_2")
    top_prop_hub = designer.add_hub(name="top_prop_hub",
                                 num_connects=2,
                                 diameter=tube_diameter,
                                 connector_horizonal_angle=180,
                                 connects=["Bottom_Connector"],
                                 mount_inst=[top_vert_prop_tube],
                                 mount_conn=["EndConnection"])
    bottom_prop_hub = designer.add_hub(name="bottom_prop_hub",
                                 num_connects=2,
                                 diameter=tube_diameter,
                                 connector_horizonal_angle=180,
                                 connects=["Top_Connector"],
                                 mount_inst=[bottom_vert_prop_tube],
                                 mount_conn=["EndConnection"])
    designer.set_named_parameter([top_vert_prop_tube], "TopVertSpread", "Length", prop_vert_spread_length_t)
    designer.set_named_parameter([bottom_vert_prop_tube], "BottomVertSpread", "Length", prop_vert_spread_length_b)

    prop_hort_spread_length = 140
    # From desired tilt_angle, on left: 360 - tilt_angle, on right: tilt_angle
    prop_tilt_angle_l = 315
    prop_tilt_angle_r = 45
    top_prop_hort_tube_l = designer.add_tube(size=tube_size,
                                         length=prop_hort_spread_length,
                                         end_rotation=prop_tilt_angle_l,
                                         name="top_prop_hort_tube_l",
                                         mount_base_inst=top_prop_hub,
                                         mount_base_conn="Side_Connector_1")
    top_prop_hort_tube_r = designer.add_tube(size=tube_size,
                                         length=prop_hort_spread_length,
                                         end_rotation=prop_tilt_angle_r,
                                         name="top_prop_hort_tube_r",
                                         mount_base_inst=top_prop_hub,
                                         mount_base_conn="Side_Connector_2")
    bottom_prop_hort_tube_l = designer.add_tube(size=tube_size,
                                         length=prop_hort_spread_length,
                                         end_rotation=prop_tilt_angle_l,
                                         name="bottom_prop_hort_tube_l",
                                         mount_base_inst=bottom_prop_hub,
                                         mount_base_conn="Side_Connector_2")
    bottom_prop_hort_tube_r = designer.add_tube(size=tube_size,
                                         length=prop_hort_spread_length,
                                         end_rotation=prop_tilt_angle_r,
                                         name="bottom_prop_hort_tube_r",
                                         mount_base_inst=bottom_prop_hub,
                                         mount_base_conn="Side_Connector_1")
                        
    designer.set_named_parameter([top_prop_hort_tube_l, bottom_prop_hort_tube_l], "LeftTiltAngle", "END_ROT", prop_tilt_angle_l)
    designer.set_named_parameter([top_prop_hort_tube_r, bottom_prop_hort_tube_r], "RightTiltAngle", "END_ROT", prop_tilt_angle_r)
    designer.set_named_parameter([top_prop_hort_tube_l, bottom_prop_hort_tube_l, top_prop_hort_tube_r, bottom_prop_hort_tube_r], "HortSpread", "Length", prop_hort_spread_length)
    top_prop_hub_l = designer.add_hub(name="top_prop_hub_l",
                                  num_connects=2,
                                  diameter=tube_diameter,
                                  connector_horizonal_angle=90,
                                  connector_vertical_angle=0,
                                  connects=["Side_Connector_1"],
                                  mount_inst=[top_prop_hort_tube_l],
                                  mount_conn=["EndConnection"])
    top_prop_hub_r = designer.add_hub(name="top_prop_hub_r",
                                  num_connects=2,
                                  diameter=tube_diameter,
                                  connector_horizonal_angle=90,
                                  connector_vertical_angle=0,
                                  connects=["Side_Connector_2"],
                                  mount_inst=[top_prop_hort_tube_r],
                                  mount_conn=["EndConnection"])
    bottom_prop_hub_l = designer.add_hub(name="bottom_prop_hub_l",
                                  num_connects=2,
                                  diameter=tube_diameter,
                                  connector_horizonal_angle=90,
                                  connector_vertical_angle=0,
                                  connects=["Side_Connector_2"],
                                  mount_inst=[bottom_prop_hort_tube_l],
                                  mount_conn=["EndConnection"])
    bottom_prop_hub_r = designer.add_hub(name="bottom_prop_hub_r",
                                  num_connects=2,
                                  diameter=tube_diameter,
                                  connector_horizonal_angle=90,
                                  connector_vertical_angle=0,
                                  connects=["Side_Connector_1"],
                                  mount_inst=[bottom_prop_hort_tube_r],
                                  mount_conn=["EndConnection"])
    prop_tilt_tube_length = 50
    top_prop_tilt_tube_l = designer.add_tube(size=tube_size,
                                             length=prop_tilt_tube_length,
                                             end_rotation=0,
                                             name="top_prop_tilt_tube_l",
                                             mount_base_inst=top_prop_hub_l,
                                             mount_base_conn="Side_Connector_2")
    top_prop_tilt_tube_r = designer.add_tube(size=tube_size,
                                             length=prop_tilt_tube_length,
                                             end_rotation=0,
                                             name="top_prop_tilt_tube_r",
                                             mount_base_inst=top_prop_hub_r,
                                             mount_base_conn="Side_Connector_1")
    top_prop_flange_l = designer.add_flange(size=tube_size,
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
    top_prop_flange_r = designer.add_flange(size=tube_size,
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
    bottom_prop_tilt_tube_l = designer.add_tube(size=tube_size,
                                             length=prop_tilt_tube_length,
                                             end_rotation=0,
                                             name="bottom_prop_tilt_tube_l",
                                             mount_base_inst=bottom_prop_hub_l,
                                             mount_base_conn="Side_Connector_1")
    bottom_prop_tilt_tube_r = designer.add_tube(size=tube_size,
                                             length=prop_tilt_tube_length,
                                             end_rotation=0,
                                             name="bottom_prop_tilt_tube_r",
                                             mount_base_inst=bottom_prop_hub_r,
                                             mount_base_conn="Side_Connector_2")
    bottom_prop_flange_l = designer.add_flange(size=tube_size,
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
    bottom_prop_flange_r = designer.add_flange(size=tube_size,
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
    designer.close_design(corpus="uav", orient_z_angle=180)


def create_tail_sitter(workflow: str, minio_name: str, num_samples: int):
    """
    This is for the UAM corpus
    """
    designer = Designer()

    # Setup Gremlin query and Jenkins interfaces
    architecture = Architect()
    architecture.open_jenkins_client(workflow)

    # Create dictionary of parameters that should vary for this design (designer knows the relationships)
    # Dictionary will have changeable parameters and a list of component instantances that uses the parameter
    # value.
    # config_parameter_list = [
    #    'wing_chord', 'bar1_length', 'bar2_length', 'stear_wing_chord']
    config_parameter_list = [
        'wing_chord', 'bar1_length', 'bar2_length']
    config_parameter_dict = dict.fromkeys(config_parameter_list, None)

    if False:
        design_name_inst = "TailSitter3NarrowBody"
        designer.create_design(design_name_inst)

        fuselage = designer.add_fuselage_uam(name="fuselage",
                                             length=2345,
                                             sphere_diameter=1201,
                                             middle_length=1517,
                                             tail_diameter=107,
                                             floor_height=110,
                                             seat_1_fb=1523,
                                             seat_1_lr=0,
                                             seat_2_fb=690,
                                             seat_2_lr=0,
                                             top_port_disp=0,
                                             bottom_port_disp=0,
                                             left_port_disp=0,
                                             right_port_disp=0)

        wing_naca = "0015"
        wing_chord = 1400
        wing_span = 8000
        wing_load = 5000

        battery_model = "VitalyBeta"
        battery_voltage = 840
        battery_percent = 100

        cylinder_diameter = 100
        port_thickness = 0.75 * cylinder_diameter
        bar1_length = 1000
        bar2_length = 750

        motor_model = "MAGiDRIVE150"
        propeller_model = "62x5_2_3200_46_1150"

        has_stear_wing = True
        stear_wing_naca = "0006"
        stear_wing_chord = 500
        stear_wing_span = 3000
        stear_wing_load = 1000

    else:
        design_name_inst = "TailSitter3JoyRide"
        designer.create_design(design_name_inst)

        fuselage = designer.add_fuselage_uam(name="fuselage",
                                             length=500,
                                             sphere_diameter=160,
                                             middle_length=400,
                                             tail_diameter=100,
                                             floor_height=130,
                                             seat_1_fb=1400,
                                             seat_1_lr=0,
                                             seat_2_fb=2300,
                                             seat_2_lr=0,
                                             port_thickness=75,
                                             left_port_disp=-550,
                                             right_port_disp=-550)

        wing_naca = "0015"
        wing_chord = 1400
        wing_span = 8000
        wing_load = 5000

        battery_model = "VitalyBeta"
        battery_voltage = 840
        battery_percent = 100

        cylinder_diameter = 100
        port_thickness = 0.75 * cylinder_diameter
        bar1_length = 700
        bar2_length = 750

        motor_model = "MAGiDRIVE150"
        propeller_model = "62x5_2_3200_46_1150"

        has_stear_wing = True
        stear_wing_naca = "0006"
        stear_wing_chord = 500
        stear_wing_span = 3000
        stear_wing_load = 1000

    designer.add_passenger(name="passenger1",
                           fuselage_inst=fuselage,
                           fuselage_conn="SEAT_1_CONNECTOR")
    designer.add_passenger(name="passenger2",
                           fuselage_inst=fuselage,
                           fuselage_conn="SEAT_2_CONNECTOR")

    right_wing = designer.add_wing_uam(name="right_wing",
                                       naca=wing_naca,
                                       chord=wing_chord,
                                       span=wing_span,
                                       load=wing_load,
                                       left_inst=fuselage,
                                       left_conn="RIGHT_CONNECTOR")
    config_parameter_dict["wing_chord"] = ["right_wing"]

    left_wing = designer.add_wing_uam(name="left_wing",
                                      naca=wing_naca,
                                      chord=wing_chord,
                                      span=wing_span,
                                      load=wing_load,
                                      right_inst=fuselage,
                                      right_conn="LEFT_CONNECTOR")
    config_parameter_dict["wing_chord"].append("left_wing")

    battery_controller = designer.add_battery_controller("battery_controller")

    designer.add_battery_uam(battery_model,
                             name="right_battery",
                             naca=wing_naca,
                             chord=wing_chord,
                             span=wing_span,
                             mount_side=1,
                             voltage_request=battery_voltage,
                             volume_percent=battery_percent,
                             wing_inst=right_wing,
                             controller_inst=battery_controller)

    designer.add_battery_uam(battery_model,
                             name="left_battery",
                             naca=wing_naca,
                             chord=wing_chord,
                             span=wing_span,
                             mount_side=2,
                             voltage_request=battery_voltage,
                             volume_percent=battery_percent,
                             wing_inst=left_wing,
                             controller_inst=battery_controller)

    top_bar = designer.add_cylinder(name="top_bar",
                                    length=bar1_length,
                                    diameter=cylinder_diameter,
                                    port_thickness=port_thickness,
                                    mount_inst=fuselage,
                                    mount_conn="TOP_CONNECTOR")
    config_parameter_dict["bar1_length"] = ["top_bar"]

    top_hub = designer.add_cylinder(name="top_hub",
                                    length=cylinder_diameter,
                                    diameter=cylinder_diameter,
                                    port_thickness=port_thickness,
                                    mount_inst=top_bar,
                                    mount_conn="REAR_CONNECTOR")

    top_right_bar = designer.add_cylinder(name="top_right_bar",
                                          length=bar2_length,
                                          diameter=cylinder_diameter,
                                          port_thickness=port_thickness,
                                          mount_inst=top_hub,
                                          mount_conn="LEFT_CONNECTOR")
    config_parameter_dict["bar2_length"] = ["top_right_bar"]

    top_right_hub = designer.add_cylinder(name="top_right_hub",
                                          length=cylinder_diameter,
                                          diameter=cylinder_diameter,
                                          port_thickness=port_thickness,
                                          mount_inst=top_right_bar,
                                          mount_conn="REAR_CONNECTOR")

    designer.add_motor_propeller(motor_model=motor_model,
                                 prop_model=propeller_model,
                                 prop_type=1,
                                 direction=1,
                                 name_prefix="top_right_front",
                                 mount_inst=top_right_hub,
                                 mount_conn="RIGHT_CONNECTOR",
                                 controller_inst=battery_controller)

    top_left_bar = designer.add_cylinder(name="top_left_bar",
                                         length=bar2_length,
                                         diameter=cylinder_diameter,
                                         port_thickness=port_thickness,
                                         mount_inst=top_hub,
                                         mount_conn="RIGHT_CONNECTOR")
    config_parameter_dict["bar2_length"].append("top_left_bar")

    top_left_hub = designer.add_cylinder(name="top_left_hub",
                                         length=cylinder_diameter,
                                         diameter=cylinder_diameter,
                                         port_thickness=port_thickness,
                                         mount_inst=top_left_bar,
                                         mount_conn="REAR_CONNECTOR")

    designer.add_motor_propeller(motor_model=motor_model,
                                 prop_model=propeller_model,
                                 prop_type=-1,
                                 direction=-1,
                                 name_prefix="top_left_front",
                                 mount_inst=top_left_hub,
                                 mount_conn="LEFT_CONNECTOR",
                                 controller_inst=battery_controller)

    bottom_bar = designer.add_cylinder(name="bottom_bar",
                                       length=bar1_length,
                                       diameter=cylinder_diameter,
                                       port_thickness=port_thickness,
                                       mount_inst=fuselage,
                                       mount_conn="BOTTOM_CONNECTOR")
    config_parameter_dict["bar1_length"] = ["bottom_bar"]

    bottom_hub = designer.add_cylinder(name="bottom_hub",
                                       length=cylinder_diameter,
                                       diameter=cylinder_diameter,
                                       port_thickness=port_thickness,
                                       mount_inst=bottom_bar,
                                       mount_conn="REAR_CONNECTOR")

    bottom_right_bar = designer.add_cylinder(name="bottom_right_bar",
                                             length=bar2_length,
                                             diameter=cylinder_diameter,
                                             port_thickness=port_thickness,
                                             mount_inst=bottom_hub,
                                             mount_conn="RIGHT_CONNECTOR")
    config_parameter_dict["bar2_length"].append("bottom_right_bar")

    bottom_right_hub = designer.add_cylinder(name="bottom_right_hub",
                                             length=cylinder_diameter,
                                             diameter=cylinder_diameter,
                                             port_thickness=port_thickness,
                                             mount_inst=bottom_right_bar,
                                             mount_conn="REAR_CONNECTOR")

    designer.add_motor_propeller(motor_model=motor_model,
                                 prop_model=propeller_model,
                                 prop_type=-1,
                                 direction=-1,
                                 name_prefix="bottom_right_front",
                                 mount_inst=bottom_right_hub,
                                 mount_conn="LEFT_CONNECTOR",
                                 controller_inst=battery_controller)

    bottom_left_bar = designer.add_cylinder(name="bottom_left_bar",
                                            length=bar2_length,
                                            diameter=cylinder_diameter,
                                            port_thickness=port_thickness,
                                            mount_inst=bottom_hub,
                                            mount_conn="LEFT_CONNECTOR")
    config_parameter_dict["bar2_length"].append("bottom_left_bar")

    bottom_left_hub = designer.add_cylinder(name="bottom_left_hub",
                                            length=cylinder_diameter,
                                            diameter=cylinder_diameter,
                                            port_thickness=port_thickness,
                                            mount_inst=bottom_left_bar,
                                            mount_conn="REAR_CONNECTOR")

    designer.add_motor_propeller(motor_model=motor_model,
                                 prop_model=propeller_model,
                                 prop_type=1,
                                 direction=1,
                                 name_prefix="bottom_left_front",
                                 mount_inst=bottom_left_hub,
                                 mount_conn="RIGHT_CONNECTOR",
                                 controller_inst=battery_controller)

    if has_stear_wing:
        stear_bar1 = designer.add_cylinder(name="stear_bar1",
                                           length=4000,
                                           diameter=cylinder_diameter,
                                           port_thickness=port_thickness,
                                           mount_inst=fuselage,
                                           mount_conn="REAR_CONNECTOR")

        stear_bar2 = designer.add_cylinder(name="stear_bar2",
                                           length=stear_wing_chord,
                                           diameter=cylinder_diameter,
                                           port_thickness=port_thickness,
                                           front_angle=45,
                                           mount_inst=stear_bar1,
                                           mount_conn="REAR_CONNECTOR")
        #config_parameter_dict["stear_wing_chord"] = ["stear_bar2"]

        designer.add_wing_uam(name="right_stear_wing",
                              naca=stear_wing_naca,
                              chord=stear_wing_chord,
                              span=stear_wing_span,
                              load=stear_wing_load,
                              left_inst=stear_bar2,
                              left_conn="RIGHT_CONNECTOR")
        # config_parameter_dict["stear_wing_chord"].append("right_stear_wing")

        designer.add_wing_uam(name="left_stear_wing",
                              naca=stear_wing_naca,
                              chord=stear_wing_chord,
                              span=stear_wing_span,
                              load=stear_wing_load,
                              left_inst=stear_bar2,
                              left_conn="TOP_CONNECTOR")
        # config_parameter_dict["stear_wing_chord"].append("left_stear_wing")

    designer.set_config_param("Requested_Lateral_Speed_1", 50)
    designer.set_config_param("Requested_Lateral_Speed_3", 32)
    designer.set_config_param("Requested_Lateral_Speed_5", 46)
    designer.set_config_param("Q_Position_5", 0.01)
    designer.set_config_param("Q_Velocity_5", 0.1)
    designer.set_config_param("Q_Angles_5", 1.0)
    designer.set_config_param("Q_Angular_Velocity_5", 0.1)
    designer.set_config_param("R_5", 0.1)

    # MM TODO: A bit of duplication here, but pushing on through for now
    design_fdm_parameters = {
        "Analysis_Type": 3,
        "Flight_Path": [1, 3, 4, 5],
        "Requested_Lateral_Speed": [50, 32, 1, 46],
        "Requested_Vertical_Speed": 19,
        "Q_Position": [1, 1, 1, 0.01],
        "Q_Velocity": [1, 1, 1, 0.1],
        "Q_Angular_Velocity": [1, 1, 1, 0.1],
        "Q_Angles": 1,
        "Ctrl_R": 0.1
    }
    architecture.set_fdm_parameters(design_fdm_parameters)

    designer.close_design()

    # Create configuration file for this design (yaml)
    # using maximum configurability with corpus defined min/max (i.e. not specifying here)
    # The structure is created in the workflow class.
    #print("config_parameter_dict: {}".format(config_parameter_dict))
    description = "Randomized Tailsitter design"

    first_param = True
    indx = 0
    for key in config_parameter_dict:
        # Since design creation is variable, make sure the value (list) for the current key is not NONE
        if config_parameter_dict[key] != None:
            #print("config_parameter_dict key: {}".format(key))
            if key == "wing_chord" or key == "stear_wing_chord":
                comp_type = "Wing"
                comp_modelname = "naca_wing"
                set_name = key + "_1"
                entry_param_name = ["CHORD_1", "CHORD_2"]
            # all other parameters are for cylinders
            else:
                comp_type = "Cylinder"
                comp_modelname = "PORTED_CYL"
                set_name = key
                entry_param_name = ["LENGTH"]
                minimum_value = 100
                maximum_value = 5000
            #print("config_parameter_dict entry: {}".format(config_parameter_dict[key]))
            if first_param:
                if comp_type == "Cylinder":
                    architecture.jenkins_client.build_study_dict(
                        design_name_inst, description, architecture.fdm_parameters, set_name, comp_type, comp_modelname, config_parameter_dict[key], entry_param_name[0], num_samples, minimum_value, maximum_value)
                else:
                    architecture.jenkins_client.build_study_dict(
                        design_name_inst, description, architecture.fdm_parameters, set_name, comp_type, comp_modelname, config_parameter_dict[key], entry_param_name[0], num_samples)
                first_param = False
            # Append parameter information
            else:
                if comp_type == "Cylinder":
                    architecture.jenkins_client.create_param_comp_entry(
                        set_name, comp_type, comp_modelname, config_parameter_dict[key], entry_param_name[0], minimum_value, maximum_value)
                else:
                    architecture.jenkins_client.create_param_comp_entry(
                        set_name, comp_type, comp_modelname, config_parameter_dict[key], entry_param_name[0])
            # For wings, chord_1 = chord_2, so create a duplicate entry
            if (len(entry_param_name) - 1) > indx:
                indx += 1
                new_set_name = key + "_2"
                architecture.jenkins_client.duplicate_param_comp_entry(
                    set_name, new_set_name, entry_param_name[indx])

    architecture.jenkins_client.write_study_config(design_name_inst)

    if (minio_name == ""):
        minio_name = architecture.jenkins_parameters.get("minioBucket")
    else:
        architecture.update_parameters("minioBucket", minio_name)

    # Create Jenkins run CSV file from previously stored configuration file (yaml)
    config_filename = design_name_inst + "_study_params.yaml"
    config_design_name = architecture.jenkins_client.create_direct2cad_csv(
        minio_name, config_filename)
    print("Jenkins run CSV file ({}) has been written".format(config_design_name))

    # For direct2cad, need to start creoson
    # if workflow == "uam_direct2cad":
    #    print("Starting CREO - architect")
    #    architecture.start_creo()

    # Run UAM_Workflow on the newly created design
    architecture.update_parameters("graphGUID", design_name_inst)
    param_filename = config_filename.replace(".yaml", ".csv")
    architecture.update_parameters("paramFile", param_filename)
    result_filename = config_filename.replace(".yaml", ".zip")
    architecture.update_parameters("resultsFileName", result_filename)
    print("Jenkins Parameter: {}".format(architecture.jenkins_parameters))

    build = architecture.jenkins_client.build_and_wait(
        workflow, architecture.jenkins_parameters)
    architecture.jenkins_client.save_results_from_build(
        build, design_name_inst)

    # Create json of all design information and add it to the Jenkins data.zip file
    architecture.open_query_client()
    design_json = architecture.client.get_design_data(design_name_inst)
    architecture.jenkins_client.add_design_json_to_results(
        design_name_inst, design_json)

    architecture.close_client()
    architecture.close_jenkins_client()


def create_vudoo():
    """
    This is for the UAM corpus.
    """
    designer = Designer()
    designer.create_design("VUdoo5")

    fuselage = designer.add_fuselage_uam(name="fuselage",
                                         length=2000,
                                         sphere_diameter=1520,
                                         middle_length=750,
                                         tail_diameter=200,
                                         floor_height=150,
                                         seat_1_fb=1000,
                                         seat_1_lr=-210,
                                         seat_2_fb=1000,
                                         seat_2_lr=210,
                                         top_port_disp=300,
                                         bottom_port_disp=300,
                                         left_port_disp=0,
                                         right_port_disp=0)

    wing_naca = "0015"
    wing_chord = 1200
    wing_span = 10000
    wing_load = 15000

    battery_model = "Tattu25AhLi"
    battery_voltage = 569   # rounded up
    battery_percent = 88 * 7000 / 10000    # rounded down

    cylinder_diameter = 100
    port_thickness = 0.75 * cylinder_diameter
    spacer1_length = 500
    spacer2_length = 1300
    spacer3_length = 2 * spacer2_length + cylinder_diameter

    motor_model = "MAGiDRIVE300"
    propeller_model = "90x8_2_2000_41_2000"

    has_stear_wing = False
    stear_wing_naca = "0006"
    stear_wing_chord = 500
    stear_wing_span = 2000
    stear_wing_load = 1000

    designer.set_config_param("Requested_Lateral_Speed_1", 48)
    designer.set_config_param("Requested_Lateral_Speed_5", 31)
    designer.set_config_param("Q_Position_5", 0.01)
    designer.set_config_param("Q_Velocity_5", 0.01)
    designer.set_config_param("Q_Angular_Velocity_5", 0.1)
    designer.set_config_param("Q_Angles_5", 0.01)
    designer.set_config_param("R_5", 0.1)

    designer.add_passenger(name="passenger1",
                           fuselage_inst=fuselage,
                           fuselage_conn="SEAT_1_CONNECTOR")
    designer.add_passenger(name="passenger2",
                           fuselage_inst=fuselage,
                           fuselage_conn="SEAT_2_CONNECTOR")

    battery_controller = designer.add_battery_controller("battery_controller")

    right_wing = designer.add_wing_uam(name="right_wing",
                                       naca=wing_naca,
                                       chord=wing_chord,
                                       span=wing_span,
                                       load=wing_load,
                                       left_inst=fuselage,
                                       left_conn="RIGHT_CONNECTOR")

    left_wing = designer.add_wing_uam(name="left_wing",
                                      naca=wing_naca,
                                      chord=wing_chord,
                                      span=wing_span,
                                      load=wing_load,
                                      right_inst=fuselage,
                                      right_conn="LEFT_CONNECTOR")

    designer.add_battery_uam(battery_model,
                             name="right_battery",
                             naca=wing_naca,
                             chord=wing_chord,
                             span=wing_span,
                             mount_side=1,
                             voltage_request=battery_voltage,
                             volume_percent=battery_percent,
                             wing_inst=right_wing,
                             controller_inst=battery_controller)

    designer.add_battery_uam(battery_model,
                             name="left_battery",
                             naca=wing_naca,
                             chord=wing_chord,
                             span=wing_span,
                             mount_side=2,
                             voltage_request=battery_voltage,
                             volume_percent=battery_percent,
                             wing_inst=left_wing,
                             controller_inst=battery_controller)

    top_bar = designer.add_cylinder(name="top_bar",
                                    length=spacer1_length,
                                    diameter=cylinder_diameter,
                                    port_thickness=port_thickness,
                                    mount_inst=fuselage,
                                    mount_conn="TOP_CONNECTOR")

    top_hub = designer.add_cylinder(name="top_hub",
                                    length=cylinder_diameter,
                                    diameter=cylinder_diameter,
                                    port_thickness=port_thickness,
                                    mount_inst=top_bar,
                                    mount_conn="REAR_CONNECTOR")

    bottom_bar = designer.add_cylinder(name="bottom_bar",
                                       length=spacer1_length,
                                       diameter=cylinder_diameter,
                                       port_thickness=port_thickness,
                                       mount_inst=fuselage,
                                       mount_conn="BOTTOM_CONNECTOR")

    bottom_hub = designer.add_cylinder(name="bottom_hub",
                                       length=cylinder_diameter,
                                       diameter=cylinder_diameter,
                                       port_thickness=port_thickness,
                                       mount_inst=bottom_bar,
                                       mount_conn="REAR_CONNECTOR")

    top_right_hub = None
    top_left_hub = None
    bottom_right_hub = None
    bottom_left_hub = None

    for count in range(0, 1):
        top_right_bar = designer.add_cylinder(name="top_right_bar{}".format(count),
                                              length=spacer2_length if count == 0 else spacer3_length,
                                              diameter=cylinder_diameter,
                                              port_thickness=port_thickness,
                                              mount_inst=top_hub if count == 0 else top_right_hub,
                                              mount_conn="LEFT_CONNECTOR" if count == 0 else "REAR_CONNECTOR")

        top_right_hub = designer.add_cylinder(name="top_right_hub{}".format(count),
                                              length=cylinder_diameter,
                                              diameter=cylinder_diameter,
                                              port_thickness=port_thickness,
                                              mount_inst=top_right_bar,
                                              mount_conn="REAR_CONNECTOR")

        designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     prop_type=1,
                                     direction=1,
                                     name_prefix="top_right_front{}".format(
                                         count),
                                     mount_inst=top_right_hub,
                                     mount_conn="RIGHT_CONNECTOR",
                                     controller_inst=battery_controller)

        designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     prop_type=1,
                                     direction=-1,
                                     name_prefix="top_right_rear{}".format(
                                         count),
                                     mount_inst=top_right_hub,
                                     mount_conn="LEFT_CONNECTOR",
                                     controller_inst=battery_controller)

        top_left_bar = designer.add_cylinder(name="top_left_bar{}".format(count),
                                             length=spacer2_length if count == 0 else spacer3_length,
                                             diameter=cylinder_diameter,
                                             port_thickness=port_thickness,
                                             mount_inst=top_hub if count == 0 else top_left_hub,
                                             mount_conn="RIGHT_CONNECTOR" if count == 0 else "REAR_CONNECTOR")

        top_left_hub = designer.add_cylinder(name="top_left_hub{}".format(count),
                                             length=cylinder_diameter,
                                             diameter=cylinder_diameter,
                                             port_thickness=port_thickness,
                                             mount_inst=top_left_bar,
                                             mount_conn="REAR_CONNECTOR")

        designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     name_prefix="top_left_front{}".format(
                                         count),
                                     prop_type=-1,
                                     direction=-1,
                                     mount_inst=top_left_hub,
                                     mount_conn="LEFT_CONNECTOR",
                                     controller_inst=battery_controller)

        designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     name_prefix="top_left_rear{}".format(
                                         count),
                                     prop_type=-1,
                                     direction=1,
                                     mount_inst=top_left_hub,
                                     mount_conn="RIGHT_CONNECTOR",
                                     controller_inst=battery_controller)

        bottom_right_bar = designer.add_cylinder(name="bottom_right_bar{}".format(count),
                                                 length=spacer2_length if count == 0 else spacer3_length,
                                                 diameter=cylinder_diameter,
                                                 port_thickness=port_thickness,
                                                 mount_inst=bottom_hub if count == 0 else bottom_right_hub,
                                                 mount_conn="RIGHT_CONNECTOR" if count == 0 else "REAR_CONNECTOR")

        bottom_right_hub = designer.add_cylinder(name="bottom_right_hub{}".format(count),
                                                 length=cylinder_diameter,
                                                 diameter=cylinder_diameter,
                                                 port_thickness=port_thickness,
                                                 mount_inst=bottom_right_bar,
                                                 mount_conn="REAR_CONNECTOR")

        designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     name_prefix="bottom_right_front{}".format(
                                         count),
                                     prop_type=-1,
                                     direction=-1,
                                     mount_inst=bottom_right_hub,
                                     mount_conn="LEFT_CONNECTOR",
                                     controller_inst=battery_controller)

        designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     name_prefix="bottom_right_rear{}".format(
                                         count),
                                     prop_type=-1,
                                     direction=1,
                                     mount_inst=bottom_right_hub,
                                     mount_conn="RIGHT_CONNECTOR",
                                     controller_inst=battery_controller)

        bottom_left_bar = designer.add_cylinder(name="bottom_left_bar{}".format(count),
                                                length=spacer2_length if count == 0 else spacer3_length,
                                                diameter=cylinder_diameter,
                                                port_thickness=port_thickness,
                                                mount_inst=bottom_hub if count == 0 else bottom_left_hub,
                                                mount_conn="LEFT_CONNECTOR" if count == 0 else "REAR_CONNECTOR")

        bottom_left_hub = designer.add_cylinder(name="bottom_left_hub{}".format(count),
                                                length=cylinder_diameter,
                                                diameter=cylinder_diameter,
                                                port_thickness=port_thickness,
                                                mount_inst=bottom_left_bar,
                                                mount_conn="REAR_CONNECTOR")

        designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     name_prefix="bottom_left_front{}".format(
                                         count),
                                     prop_type=1,
                                     direction=1,
                                     mount_inst=bottom_left_hub,
                                     mount_conn="RIGHT_CONNECTOR",
                                     controller_inst=battery_controller)

        designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     name_prefix="bottom_left_rear{}".format(
                                         count),
                                     prop_type=1,
                                     direction=-1,
                                     mount_inst=bottom_left_hub,
                                     mount_conn="LEFT_CONNECTOR",
                                     controller_inst=battery_controller)

    if has_stear_wing:
        stear_bar1 = designer.add_cylinder(name="stear_bar1",
                                           length=4000,
                                           diameter=cylinder_diameter,
                                           port_thickness=port_thickness,
                                           mount_inst=fuselage,
                                           mount_conn="REAR_CONNECTOR")

        stear_bar2 = designer.add_cylinder(name="stear_bar2",
                                           length=stear_wing_chord,
                                           diameter=cylinder_diameter,
                                           port_thickness=port_thickness,
                                           front_angle=45,
                                           mount_inst=stear_bar1,
                                           mount_conn="REAR_CONNECTOR")

        designer.add_wing_uam(name="right_stear_wing",
                              naca=stear_wing_naca,
                              chord=stear_wing_chord,
                              span=stear_wing_span,
                              load=stear_wing_load,
                              left_inst=stear_bar2,
                              left_conn="RIGHT_CONNECTOR")

        designer.add_wing_uam(name="left_stear_wing",
                              naca=stear_wing_naca,
                              chord=stear_wing_chord,
                              span=stear_wing_span,
                              load=stear_wing_load,
                              left_inst=stear_bar2,
                              left_conn="TOP_CONNECTOR")

    designer.close_design()


def create_vari_vudoo(num_designs: int, design_name: str, workflow: str, minio_name: str, num_samples: int):
    """
    This is for the UAM corpus.
    Create a Vudoo based design, but the parameters are randomize to create
    a unique design each time. User should supply the number of designs
    desired and the base design name.  All designs will be added to the graph.
    The workflow is the Jenkins workflow that will be run on each design.
    """
    # Setup Gremlin query and Jenkins interfaces
    architecture = Architect()
    architecture.open_jenkins_client(workflow)
    # if workflow == "uam_direct2cad":
    #    architecture.connect_creoson_server()

    for x in range(num_designs):
        design_name_inst = design_name + str(x)

        designer = Designer()
        designer.create_design(design_name_inst)

        # Note (prior to 10/2022): There are two fuselages, with differing parameter names
        # Current designer.add_fuselage_uam is for the "FUSE_SPHERE_CYL_CONE" version,
        # not the NACA_Fuse. This can be randomized in the future when
        # designer.add_fuselage_uam is made more generic. For now, assuming only
        # 1 option available.
        fuse_params = get_component_parameters(
            "Fuselage", "FUSE_SPHERE_CYL_CONE")
        # RAND: rand_fuse_params = randomize_parameters(fuse_params)
        rand_fuse_params = get_corpus_assigned_parameters(fuse_params)

        # RAND: fuse_length = round(float(rand_fuse_params[0]["LENGTH"]["assigned"]))
        # RAND: fuse_sphere_diameter = round(
        # RAND:     float(rand_fuse_params[0]["SPHERE_DIAMETER"]["assigned"]))
        # RAND: fuse_middle_length = round(
        # RAND:     float(rand_fuse_params[0]["MIDDLE_LENGTH"]["assigned"]))
        # RAND: fuse_tail_diameter = round(
        # RAND:     float(rand_fuse_params[0]["TAIL_DIAMETER"]["assigned"]))
        # RAND: fuse_floor_height = round(
        # RAND:     float(rand_fuse_params[0]["FLOOR_HEIGHT"]["assigned"]))
        # RAND: fuse_seat_1_fb = round(
        # RAND:     float(rand_fuse_params[0]["SEAT_1_FB"]["assigned"]))
        # RAND: fuse_seat_1_lr = round(
        # RAND:     float(rand_fuse_params[0]["SEAT_1_LR"]["assigned"]))
        # RAND: fuse_seat_2_fb = round(
        # RAND:     float(rand_fuse_params[0]["SEAT_2_FB"]["assigned"]))
        # RAND: fuse_seat_2_lr = round(
        # RAND:     float(rand_fuse_params[0]["SEAT_2_LR"]["assigned"]))
        # RAND: fuse_top_port_disp = round(
        # RAND:     float(rand_fuse_params[0]["TOP_PORT_DISP"]["assigned"]))
        # RAND: fuse_bottom_port_disp = round(
        # RAND:     float(rand_fuse_params[0]["BOTTOM_PORT_DISP"]["assigned"]))
        # RAND: fuse_left_port_disp = round(
        # RAND:     float(rand_fuse_params[0]["LEFT_PORT_DISP"]["assigned"]))
        # RAND: fuse_right_port_disp = round(
        # RAND:     float(rand_fuse_params[0]["RIGHT_PORT_DISP"]["assigned"]))

        fuse_length = 2000
        fuse_sphere_diameter = 1520
        fuse_middle_length = 750
        fuse_tail_diameter = 200
        fuse_floor_height = 150
        fuse_seat_1_fb = 1000
        fuse_seat_1_lr = -210
        fuse_seat_2_fb = 1000
        fuse_seat_2_lr = 210
        fuse_top_port_disp = 300
        fuse_bottom_port_disp = 300
        fuse_left_port_disp = 0
        fuse_right_port_disp = 0
        # print("Fuselage length, sphere diameter, middle length, tail diameter: %f, %f, %f, %f" % (fuse_length, fuse_sphere_diameter, fuse_middle_length, fuse_tail_diameter))
        # print("Fuselage floor height, seat 1 fb/lr, seat 2 fb/lr: %f, %f,%f,%f,%f" % (fuse_floor_height, fuse_seat_1_fb, fuse_seat_1_lr, fuse_seat_2_fb, fuse_seat_2_lr))
        # print("Fuselage ports - top/bottom/left/right: %f, %f, %f, %f" % (fuse_top_port_disp, fuse_bottom_port_disp, fuse_left_port_disp, fuse_right_port_disp))

        fuselage = designer.add_fuselage_uam(name="fuselage",
                                             length=fuse_length,
                                             sphere_diameter=fuse_sphere_diameter,
                                             middle_length=fuse_middle_length,
                                             tail_diameter=fuse_tail_diameter,
                                             floor_height=fuse_floor_height,
                                             seat_1_fb=fuse_seat_1_fb,
                                             seat_1_lr=fuse_seat_1_lr,
                                             seat_2_fb=fuse_seat_2_fb,
                                             seat_2_lr=fuse_seat_2_lr,
                                             top_port_disp=fuse_top_port_disp,
                                             bottom_port_disp=fuse_bottom_port_disp,
                                             left_port_disp=fuse_left_port_disp,
                                             right_port_disp=fuse_right_port_disp)

        # Randomize wing parameters
        wing_params = get_component_parameters("Wing", "naca_wing")
        # RAND: rand_wing_params = randomize_parameters(wing_params)
        rand_wing_params = get_corpus_assigned_parameters(wing_params)

        # This parameter (NACA_Profile) does not have a min/max in the corpus_data.json
        # But there is a set of NACA tables in c:/jwork/Agents/workspace/UAM_Workflows/Tables/aero_info.json
        # We could use this file to randomly select a value.  Leaving the fixed value for now.

        # RAND: wing_naca = rand_wing_params[0]["NACA_Profile"]["assigned"]
        # RAND: wing_naca = random_naca_profile_selection()
        wing_naca = "0015"
        # CHORD_1 and CHORD_2 should be the same, using randomized CHORD_1 for this value
        # RAND: wing_chord = round(float(rand_wing_params[0]["CHORD_1"]["assigned"]))
        # RAND: wing_span = round(float(rand_wing_params[0]["SPAN"]["assigned"]))
        # RAND: wing_load = round(float(rand_wing_params[0]["LOAD"]["assigned"]))
        wing_chord = 1200
        wing_span = 10000
        wing_load = 15000
        # print("Wing Chord, span, load, NACA profile: %f, %f, %f %s" % (wing_chord, wing_span, wing_load, wing_naca))

        # Wing parameters not set with parameters:
        #     AILERON_BIAS,
        #     FLAP_BIAS,
        #     TAPER_OFFSET (user defined in Creo, did not observe impact to design),
        #     THICKNESS (set by wing_naca)

        # Randomize batteries and the parameters
        # RAND: battery_model = random_component_selection("Battery")
        battery_model = "Tattu25AhLi"
        battery_params = get_component_parameters("Battery", battery_model)
        # RAND: rand_battery_params = randomize_parameters(battery_params)
        rand_battery_params = get_corpus_assigned_parameters(battery_params)

        battery_voltage = 569   # rounded up
        battery_percent = 88 * 7000 / 10000    # rounded down
        # RAND: battery_voltage = math.ceil(
        # RAND:    float(rand_battery_params[0]["VOLTAGE_REQUEST"]["assigned"]))   # rounded up
        # RAND: battery_percent = math.floor(
        # RAND:    float(rand_battery_params[0]["VOLUME_PERCENT"]["assigned"]))   # rounded down
        # battery_mount_side = round(float(rand_battery_params[0]["MOUNT_SIDE"]["assigned"]))
        # print("Battery voltage, percent: %f, %f" % (battery_voltage, battery_percent))

        # Battery parameters set with wing parameters:
        #    CHORD1 / CHORD2, SPAN, THICKNESS (using wing_naca)
        # Battery parameter not set with battery parameters:
        #    TAPER_OFFSET

        # Randomize cylinder and the parameters. There are two cylinders, assume same diameter
        # so use rand_cyl1_params for common parameters (use second set for LENGTH).
        # Check that the cylinder parameters are valid, if not retry
        cyl_params = get_component_parameters("Cylinder", "PORTED_CYL")
        valid_cylinder = False
        while not valid_cylinder:
            # RAND: rand_cyl1_params = randomize_parameters(cyl_params)
            rand_cyl1_params = randomize_cyl_length(cyl_params)
            # print(rand_cyl1_params)
            # RAND: cylinder_diameter = round(
            # RAND:     float(rand_cyl1_params["DIAMETER"]["assigned"]))
            cylinder_diameter = 100
            spacer1_length = 500
            # RAND: spacer1_length = round(
            # RAND:     float(rand_cyl1_params["LENGTH"]["assigned"]))
            # RAND: port_thickness = round(
            # RAND:     float(rand_cyl1_params["PORT_THICKNESS"]["assigned"]))
            port_thickness = 0.75 * cylinder_diameter

            valid_cylinder = 8 <= port_thickness < cylinder_diameter <= spacer1_length
            if valid_cylinder:
                print("Cylinder 1: Valid length found (%f)" % spacer1_length)
            else:
                print("Cylinder 1: Invalid length (%f). Try again" %
                      spacer1_length)

        valid_cylinder = False
        while not valid_cylinder:
            # Spacer3 is related to spacer2 (*2) and the result needs to be less than expected cylinder max (5000)
            # RAND: rand_cyl2_params = randomize_parameters(cyl_params)
            # Spacer3 is related to spacer2 and the result needs to be less than expected cylinder max
            rand_cyl2_params = randomize_cyl_length(cyl_params, 0.5)
            # print(rand_cyl2_params)
            # RAND: spacer2_length = round(
            # RAND:     float(rand_cyl2_params["LENGTH"]["assigned"]))
            spacer2_length = 1300
            spacer3_length = 2 * spacer2_length + cylinder_diameter
            valid_cylinder = 8 <= port_thickness < cylinder_diameter <= spacer2_length
            if valid_cylinder:
                print("Cylinder 2: Valid length found (%f)" % spacer2_length)
            else:
                print("Cylinder 2: Invalid length (%f). Try again" %
                      spacer2_length)

        # print("Cyl Diameter, Spacer1, Spacer2: %f, %f, %f" % (cylinder_diameter, spacer1_length, spacer2_length))

        # Randomize motor selection
        motor_model = "MAGiDRIVE300"
        # RAND: motor_model = random_component_selection("Motor")
        # print("Motor: %s" % motor_model)

        # Randomize propeller selection
        propeller_model = "90x8_2_2000_41_2000"
        # RAND: propeller_model = random_component_selection("Propeller")
        # print("Propeller: %s" % propeller_model)

        # Propeller parameter not set with propeller parameters, but fixed based on design approach:
        #     Direction
        #     Prop_type

        # Determine prop/motor setup - there is an 8 propeller set that can be replicated
        # The set is made up of 4 front propellers and 4 rear propellers
        # The random setup for a prop/motor set (or prop_set) will be one of four configurations:
        #     4 Front props/motors, 4
        max_num_prop_sets = 12
        num_prop_sets = round(random.uniform(0, max_num_prop_sets))

        prop_set_config = ["Front", "Rear", "All", "None"]
        print("Number of Propeller/Motor sets: %d" % num_prop_sets)

        # Randomize stear wing parameters
        has_stear_wing = bool(random.getrandbits(1))

        # MM DEBUG:
        #num_prop_sets = 1
        #has_stear_wing = "True"

        print("Presence of Stear Wing: %s" % has_stear_wing)
        stear_wing_params = get_component_parameters("Wing", "naca_wing")
        # RAND: rand_stear_wing_params = randomize_parameters(stear_wing_params)
        rand_stear_wing_params = get_corpus_assigned_parameters(
            stear_wing_params)
        # print(rand_stear_wing_params)

        # This parameter (NACA_Profile) does not have a min/max in the corpus_data.json
        # But there is a set of NACA tables in c:/jwork/Agents/workspace/UAM_Workflows/Tables/aero_info.json
        # We could use this file to randomly select a value.  Leaving the fixed value for now.
        # RAND: stear_wing_naca = random_naca_profile_selection()
        # RAND: stear_wing_naca = rand_stear_wing_params[0]["NACA_Profile"]["assigned"]
        stear_wing_naca = "0006"

        # CHORD_1 and CHORD_2 should be the same, using randomized CHORD_1 for this value
        # RAND: stear_wing_chord = round(
        # RAND:     float(rand_stear_wing_params[0]["CHORD_1"]["assigned"]))
        # RAND: stear_wing_span = round(
        # RAND:     float(rand_stear_wing_params[0]["SPAN"]["assigned"]))
        # RAND: stear_wing_load = round(
        # RAND:     float(rand_stear_wing_params[0]["LOAD"]["assigned"]))
        stear_wing_chord = 500
        stear_wing_span = 2000
        stear_wing_load = 1000
        # print("Stear Wing Chord, span, load: %f, %f, %f" % (stear_wing_chord, stear_wing_span, stear_wing_load))

        valid_cylinder = False
        while not valid_cylinder:
            # RAND: rand_bar_params = randomize_parameters(cyl_params)
            rand_bar_params = randomize_cyl_length(cyl_params)
            # print(rand_bar_params)
            # RAND: stear_bar1_length = round(
            # RAND:    float(rand_bar_params["LENGTH"]["assigned"]))
            stear_bar1_length = 4000
            # Angle was set to 45 degrees in original design, randomizing here
            # RAND: stear_bar2_front_angle = round(
            # RAND:    float(rand_bar_params["FRONT_ANGLE"]["assigned"]))
            stear_bar2_front_angle = 45
            valid_cylinder = 8 <= port_thickness < cylinder_diameter <= stear_bar1_length
            if valid_cylinder:
                print("Stear Bar 1: Valid length found (%f)" %
                      stear_bar1_length)
            else:
                print("Stear Bar 1: Invalid length (%f). Try again" %
                      stear_bar1_length)

        # print("Stear Bar Length1, Front Angle2: %f, %f" % (stear_bar1_length, stear_bar2_front_angle))

        # Create dictionary of parameters that should vary for this design (designer knows the relationships)
        # Dictionary will have changeable parameters and a list of component instantances that uses the parameter
        # value.
        config_parameter_list = [
            'wing_chord', 'spacer1_length', 'spacer2_length', 'stear_bar1_length']
        config_parameter_dict = dict.fromkeys(config_parameter_list, None)

        designer.set_config_param("Requested_Lateral_Speed_1", 48)
        designer.set_config_param("Requested_Lateral_Speed_5", 31)
        designer.set_config_param("Q_Position_5", 0.01)
        designer.set_config_param("Q_Velocity_5", 0.01)
        designer.set_config_param("Q_Angular_Velocity_5", 0.1)
        designer.set_config_param("Q_Angles_5", 0.01)
        designer.set_config_param("R_5", 0.1)

        designer.add_passenger(name="passenger1",
                               fuselage_inst=fuselage,
                               fuselage_conn="SEAT_1_CONNECTOR")
        designer.add_passenger(name="passenger2",
                               fuselage_inst=fuselage,
                               fuselage_conn="SEAT_2_CONNECTOR")

        battery_controller = designer.add_battery_controller(
            "battery_controller")

        right_wing = designer.add_wing_uam(name="right_wing",
                                           naca=wing_naca,
                                           chord=wing_chord,
                                           span=wing_span,
                                           load=wing_load,
                                           left_inst=fuselage,
                                           left_conn="RIGHT_CONNECTOR")
        config_parameter_dict["wing_chord"] = ["right_wing"]

        left_wing = designer.add_wing_uam(name="left_wing",
                                          naca=wing_naca,
                                          chord=wing_chord,
                                          span=wing_span,
                                          load=wing_load,
                                          right_inst=fuselage,
                                          right_conn="LEFT_CONNECTOR")
        config_parameter_dict["wing_chord"].append("left_wing")

        designer.add_battery_uam(battery_model,
                                 name="right_battery",
                                 naca=wing_naca,
                                 chord=wing_chord,
                                 span=wing_span,
                                 mount_side=1,
                                 voltage_request=battery_voltage,
                                 volume_percent=battery_percent,
                                 wing_inst=right_wing,
                                 controller_inst=battery_controller)

        designer.add_battery_uam(battery_model,
                                 name="left_battery",
                                 naca=wing_naca,
                                 chord=wing_chord,
                                 span=wing_span,
                                 mount_side=2,
                                 voltage_request=battery_voltage,
                                 volume_percent=battery_percent,
                                 wing_inst=left_wing,
                                 controller_inst=battery_controller)

        top_bar = designer.add_cylinder(name="top_bar",
                                        length=spacer1_length,
                                        diameter=cylinder_diameter,
                                        port_thickness=port_thickness,
                                        mount_inst=fuselage,
                                        mount_conn="TOP_CONNECTOR")
        config_parameter_dict['spacer1_length'] = ["top_bar"]

        top_hub = designer.add_cylinder(name="top_hub",
                                        length=cylinder_diameter,
                                        diameter=cylinder_diameter,
                                        port_thickness=port_thickness,
                                        mount_inst=top_bar,
                                        mount_conn="REAR_CONNECTOR")

        bottom_bar = designer.add_cylinder(name="bottom_bar",
                                           length=spacer1_length,
                                           diameter=cylinder_diameter,
                                           port_thickness=port_thickness,
                                           mount_inst=fuselage,
                                           mount_conn="BOTTOM_CONNECTOR")
        config_parameter_dict['spacer1_length'].append("bottom_bar")

        bottom_hub = designer.add_cylinder(name="bottom_hub",
                                           length=cylinder_diameter,
                                           diameter=cylinder_diameter,
                                           port_thickness=port_thickness,
                                           mount_inst=bottom_bar,
                                           mount_conn="REAR_CONNECTOR")

        top_right_hub = None
        top_left_hub = None
        bottom_right_hub = None
        bottom_left_hub = None

        if num_prop_sets > 0:
            for count in range(0, num_prop_sets):
                selected_prop_set_config = random.choice(prop_set_config)
                print("Propeller/Motor Configuration: %s" %
                      selected_prop_set_config)
                if selected_prop_set_config != "None":
                    #print("Add cylinders for top right")
                    top_right_bar = designer.add_cylinder(name="top_right_bar{}".format(count),
                                                          length=spacer2_length if count == 0 else spacer3_length,
                                                          diameter=cylinder_diameter,
                                                          port_thickness=port_thickness,
                                                          mount_inst=top_hub if count == 0 else top_right_hub,
                                                          mount_conn="LEFT_CONNECTOR" if count == 0 else "REAR_CONNECTOR")
                    if config_parameter_dict['spacer2_length'] == None:
                        config_parameter_dict['spacer2_length'] = [
                            "top_right_bar{}".format(count)]
                    else:
                        config_parameter_dict['spacer2_length'].append(
                            "top_right_bar{}".format(count))

                    top_right_hub = designer.add_cylinder(name="top_right_hub{}".format(count),
                                                          length=cylinder_diameter,
                                                          diameter=cylinder_diameter,
                                                          port_thickness=port_thickness,
                                                          mount_inst=top_right_bar,
                                                          mount_conn="REAR_CONNECTOR")

                    # Add motor/propellers for "Front" and "All" configurations
                    if selected_prop_set_config != "Rear":
                        #print("Add motor/propeller for top right front")
                        designer.add_motor_propeller(motor_model=motor_model,
                                                     prop_model=propeller_model,
                                                     prop_type=1,
                                                     direction=1,
                                                     name_prefix="top_right_front{}".format(
                                                         count),
                                                     mount_inst=top_right_hub,
                                                     mount_conn="RIGHT_CONNECTOR",
                                                     controller_inst=battery_controller)
                    # Add motor/propellers for "Rear" and "All" configuration
                    if selected_prop_set_config != "Front":
                        #print("Add motor/propeller for top right rear")
                        designer.add_motor_propeller(motor_model=motor_model,
                                                     prop_model=propeller_model,
                                                     prop_type=1,
                                                     direction=-1,
                                                     name_prefix="top_right_rear{}".format(
                                                         count),
                                                     mount_inst=top_right_hub,
                                                     mount_conn="LEFT_CONNECTOR",
                                                     controller_inst=battery_controller)

                    #print("Add cylinders for top left")
                    top_left_bar = designer.add_cylinder(name="top_left_bar{}".format(count),
                                                         length=spacer2_length if count == 0 else spacer3_length,
                                                         diameter=cylinder_diameter,
                                                         port_thickness=port_thickness,
                                                         mount_inst=top_hub if count == 0 else top_left_hub,
                                                         mount_conn="RIGHT_CONNECTOR" if count == 0 else "REAR_CONNECTOR")
                    config_parameter_dict['spacer2_length'].append(
                        "top_left_bar{}".format(count))

                    top_left_hub = designer.add_cylinder(name="top_left_hub{}".format(count),
                                                         length=cylinder_diameter,
                                                         diameter=cylinder_diameter,
                                                         port_thickness=port_thickness,
                                                         mount_inst=top_left_bar,
                                                         mount_conn="REAR_CONNECTOR")

                    # Add motor_propellers for "Front" and "All" configuration
                    if selected_prop_set_config != "Rear":
                        #print("Add motor/propeller for top left front")
                        designer.add_motor_propeller(motor_model=motor_model,
                                                     prop_model=propeller_model,
                                                     name_prefix="top_left_front{}".format(
                                                         count),
                                                     prop_type=-1,
                                                     direction=-1,
                                                     mount_inst=top_left_hub,
                                                     mount_conn="LEFT_CONNECTOR",
                                                     controller_inst=battery_controller)
                    # Add motor/propellers for "Rear" and "All" configuration
                    if selected_prop_set_config != "Front":
                        #print("Add motor/propeller for top left rear")
                        designer.add_motor_propeller(motor_model=motor_model,
                                                     prop_model=propeller_model,
                                                     name_prefix="top_left_rear{}".format(
                                                         count),
                                                     prop_type=-1,
                                                     direction=1,
                                                     mount_inst=top_left_hub,
                                                     mount_conn="RIGHT_CONNECTOR",
                                                     controller_inst=battery_controller)

                    #print("Add cylinders for bottom right")
                    bottom_right_bar = designer.add_cylinder(name="bottom_right_bar{}".format(count),
                                                             length=spacer2_length if count == 0 else spacer3_length,
                                                             diameter=cylinder_diameter,
                                                             port_thickness=port_thickness,
                                                             mount_inst=bottom_hub if count == 0 else bottom_right_hub,
                                                             mount_conn="RIGHT_CONNECTOR" if count == 0 else "REAR_CONNECTOR")
                    config_parameter_dict['spacer2_length'].append(
                        "bottom_right_bar{}".format(count))

                    bottom_right_hub = designer.add_cylinder(name="bottom_right_hub{}".format(count),
                                                             length=cylinder_diameter,
                                                             diameter=cylinder_diameter,
                                                             port_thickness=port_thickness,
                                                             mount_inst=bottom_right_bar,
                                                             mount_conn="REAR_CONNECTOR")

                    # Add motor_propellers for "Front" and "All" configuration
                    if selected_prop_set_config != "Rear":
                        #print("Add motor/propeller for bottom right front")
                        designer.add_motor_propeller(motor_model=motor_model,
                                                     prop_model=propeller_model,
                                                     name_prefix="bottom_right_front{}".format(
                                                         count),
                                                     prop_type=-1,
                                                     direction=-1,
                                                     mount_inst=bottom_right_hub,
                                                     mount_conn="LEFT_CONNECTOR",
                                                     controller_inst=battery_controller)
                    # Add motor/propellers for "Rear" and "All" configuration
                    if selected_prop_set_config != "Front":
                        #print("Add motor/propeller for bottom right rear")
                        designer.add_motor_propeller(motor_model=motor_model,
                                                     prop_model=propeller_model,
                                                     name_prefix="bottom_right_rear{}".format(
                                                         count),
                                                     prop_type=-1,
                                                     direction=1,
                                                     mount_inst=bottom_right_hub,
                                                     mount_conn="RIGHT_CONNECTOR",
                                                     controller_inst=battery_controller)

                    #print("Add cylinders for bottom left")
                    bottom_left_bar = designer.add_cylinder(name="bottom_left_bar{}".format(count),
                                                            length=spacer2_length if count == 0 else spacer3_length,
                                                            diameter=cylinder_diameter,
                                                            port_thickness=port_thickness,
                                                            mount_inst=bottom_hub if count == 0 else bottom_left_hub,
                                                            mount_conn="LEFT_CONNECTOR" if count == 0 else "REAR_CONNECTOR")
                    config_parameter_dict['spacer2_length'].append(
                        "bottom_left_bar{}".format(count))

                    bottom_left_hub = designer.add_cylinder(name="bottom_left_hub{}".format(count),
                                                            length=cylinder_diameter,
                                                            diameter=cylinder_diameter,
                                                            port_thickness=port_thickness,
                                                            mount_inst=bottom_left_bar,
                                                            mount_conn="REAR_CONNECTOR")

                    # Add motor_propellers for "Front" and "All" configuration
                    if selected_prop_set_config != "Rear":
                        #print("Add motor/propeller for bottom left front")
                        designer.add_motor_propeller(motor_model=motor_model,
                                                     prop_model=propeller_model,
                                                     name_prefix="bottom_left_front{}".format(
                                                         count),
                                                     prop_type=1,
                                                     direction=1,
                                                     mount_inst=bottom_left_hub,
                                                     mount_conn="RIGHT_CONNECTOR",
                                                     controller_inst=battery_controller)
                    # Add motor/propellers for "Rear" and "All" configuration
                    if selected_prop_set_config != "Front":
                        #print("Add motor/propeller for bottom left rear")
                        designer.add_motor_propeller(motor_model=motor_model,
                                                     prop_model=propeller_model,
                                                     name_prefix="bottom_left_rear{}".format(
                                                         count),
                                                     prop_type=1,
                                                     direction=-1,
                                                     mount_inst=bottom_left_hub,
                                                     mount_conn="LEFT_CONNECTOR",
                                                     controller_inst=battery_controller)

            if has_stear_wing:
                stear_bar1 = designer.add_cylinder(name="stear_bar1",
                                                   length=stear_bar1_length,
                                                   diameter=cylinder_diameter,
                                                   port_thickness=port_thickness,
                                                   mount_inst=fuselage,
                                                   mount_conn="REAR_CONNECTOR")
                config_parameter_dict['stear_bar1_length'] = ["stear_bar1"]

                stear_bar2 = designer.add_cylinder(name="stear_bar2",
                                                   length=stear_wing_chord,
                                                   diameter=cylinder_diameter,
                                                   port_thickness=port_thickness,
                                                   front_angle=stear_bar2_front_angle,
                                                   mount_inst=stear_bar1,
                                                   mount_conn="REAR_CONNECTOR")

                designer.add_wing_uam(name="right_stear_wing",
                                      naca=stear_wing_naca,
                                      chord=stear_wing_chord,
                                      span=stear_wing_span,
                                      load=stear_wing_load,
                                      left_inst=stear_bar2,
                                      left_conn="RIGHT_CONNECTOR")

                designer.add_wing_uam(name="left_stear_wing",
                                      naca=stear_wing_naca,
                                      chord=stear_wing_chord,
                                      span=stear_wing_span,
                                      load=stear_wing_load,
                                      left_inst=stear_bar2,
                                      left_conn="TOP_CONNECTOR")

        designer.close_design()

        # Create configuration file for this design (yaml)
        # using maximum configurability with corpus defined min/max (i.e. not specifying here)
        # The structure is created in the workflow class.
        #print("config_parameter_dict: {}".format(config_parameter_dict))
        description = "Vari-Vudoo design"

        first_param = True
        indx = 0
        for key in config_parameter_dict:
            # Since design creation is variable, make sure the value (list) for the current key is not NONE
            if config_parameter_dict[key] != None:
                #print("config_parameter_dict key: {}".format(key))
                if key == "wing_chord":
                    comp_type = "Wing"
                    comp_modelname = "naca_wing"
                    set_name = key + "_1"
                    entry_param_name = ["CHORD_1", "CHORD_2"]
                # all other parameters are for cylinders
                else:
                    comp_type = "Cylinder"
                    comp_modelname = "PORTED_CYL"
                    set_name = key
                    entry_param_name = ["LENGTH"]
                    minimum_value = 100
                    maximum_value = 5000
                #print("config_parameter_dict entry: {}".format(config_parameter_dict[key]))
                if first_param:
                    if comp_type == "Cylinder":
                        architecture.jenkins_client.build_study_dict(
                            design_name_inst, description, architecture.fdm_parameters, set_name, comp_type, comp_modelname, config_parameter_dict[key], entry_param_name[0], num_samples, minimum_value, maximum_value)
                    else:
                        architecture.jenkins_client.build_study_dict(
                            design_name_inst, description, architecture.fdm_parameters, set_name, comp_type, comp_modelname, config_parameter_dict[key], entry_param_name[0], num_samples)
                    first_param = False
                # Append parameter information
                else:
                    if comp_type == "Cylinder":
                        architecture.jenkins_client.create_param_comp_entry(
                            set_name, comp_type, comp_modelname, config_parameter_dict[key], entry_param_name[0], minimum_value, maximum_value)
                    else:
                        architecture.jenkins_client.create_param_comp_entry(
                            set_name, comp_type, comp_modelname, config_parameter_dict[key], entry_param_name[0])
                # For wings, chord_1 = chord_2, so create a duplicate entry
                if (len(entry_param_name) - 1) > indx:
                    indx += 1
                    new_set_name = key + "_2"
                    architecture.jenkins_client.duplicate_param_comp_entry(
                        set_name, new_set_name, entry_param_name[indx])

        architecture.jenkins_client.write_study_config(design_name_inst)

        if (minio_name == ""):
            minio_name = architecture.jenkins_parameters.get("minioBucket")
        else:
            architecture.update_parameters("minioBucket", minio_name)

        # Create Jenkins run CSV file from previously stored configuration file (yaml)
        config_filename = design_name_inst + "_study_params.yaml"
        config_design_name = architecture.jenkins_client.create_direct2cad_csv(
            minio_name, config_filename)
        print("Jenkins run CSV file ({}) has been written".format(config_design_name))

        # For direct2cad, need to start creoson
        # if workflow == "uam_direct2cad":
        #    print("Starting CREO - architect")
        #    architecture.start_creo()

        # Run UAM_Workflow on the newly created design
        architecture.update_parameters("graphGUID", design_name_inst)
        param_filename = config_filename.replace(".yaml", ".csv")
        architecture.update_parameters("paramFile", param_filename)
        result_filename = config_filename.replace(".yaml", ".zip")
        architecture.update_parameters("resultsFileName", result_filename)
        print("Jenkins Parameter: {}".format(architecture.jenkins_parameters))

        build = architecture.jenkins_client.build_and_wait(
            workflow, architecture.jenkins_parameters)
        architecture.jenkins_client.save_results_from_build(
            build, design_name_inst)

        # Create json of all design information and add it to the Jenkins data.zip file
        architecture.open_query_client()
        design_json = architecture.client.get_design_data(design_name_inst)
        architecture.jenkins_client.add_design_json_to_results(
            design_name_inst, design_json)

        # For uam_direct2cad, grab the partMass.json and partLocs.json files from the workflow directory
        # and add it to the data.zip
        # MM: removed (9/1/2022) when added parameter sweep capability,
        #     these files are overwritten on each sweep run - so would only retrieve the last set
        # if workflow == "uam_direct2cad":
        #    architecture.jenkins_client.grab_extra_jsons_direct2cad(
        #        design_name_inst)
        # In between runs, creoson should be stopped and started again, so stopping here
        # architecture.stop_creoson()

        # Consider removing design after each run
        # architecture.client.delete_design(design_name_inst)
        architecture.close_client()

    architecture.close_jenkins_client()
    # architecture.disconnect_creoson_server()


def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('design', choices=[
        "minimal",
        "tail-sitter",
        "vudoo",
        "vari-vudoo",
        "random-existing",
        "newaxe-cargo",
        "testquad-cargo",
        "pickaxe",
        "superquad",
        "inline-uav",
        "uno-inline-uav",
        "tiltie"
    ])
    parser.add_argument('--corpus', choices=["uam", "uav"],
                        help="indicate corpus name")

    parser.add_argument('--variable-design-name', type=str,
                        help="indicates base design name when create multiple designs with randomized parameters")
    parser.add_argument('--num-designs', type=int,
                        help="indicates number of designs to create")

    parser.add_argument('--num-samples', type=int,
                        help="indicates number of samples to run a each created design")

    # Currently only used in random_existing (uam_direct2cad workflow)
    parser.add_argument('--config-file', type=str,
                        help="indicates name of the yaml config file that defines the randomization for the runs")

    # Currently only used with vari-vudoo
    parser.add_argument('--workbench', choices=["UAM_Workflows", "uam_direct2cad"],
                        help="indicates which workflow to run when creating designs")

    # Arguments for uam_direct2cad
    parser.add_argument('--bucket', type=str, metavar='minio',
                        help="indicates the minio bucket where the parameter file is located")

    args = parser.parse_args(args)

    # Default workflow
    aWorkflow = "UAM_Workflows"
    if args.workbench:
        aWorkflow = args.workbench

    # Additional parameters for running uam_direct2cad workflow
    minio_bucket = ""
    if args.bucket:
        minio_bucket = args.bucket
    if args.num_samples:
        number_samples = args.num_samples
    else:
        number_samples = 1

    if args.design == "minimal":
        if args.corpus == "uam" or args.corpus == "UAM":
            create_minimal_uam()
        elif args.corpus == "uav" or args.corpus == "UAV":
            create_minimal_uav()
        else:
            print("Please indicate a corpus (--corpus)")
    elif args.design == "tail-sitter":
        create_tail_sitter(aWorkflow, minio_bucket, number_samples)
    elif args.design == "vudoo":
        create_vudoo()
    elif args.design == "vari-vudoo":
        if args.variable_design_name and args.num_designs:
            name = args.variable_design_name
            number_designs = args.num_designs
            create_vari_vudoo(number_designs, name, aWorkflow,
                              minio_bucket, number_samples)
        else:
            print(
                "Please indicate the base design name (--variable-design-name) and number of designs (--num-designs")
    elif args.design == "random-existing":
        if args.config_file:
            config = args.config_file
            # At this time (8/30/22), this option only works for uam_direct2cad workflow
            # Providing minio_bucket name is optional
            randomize_existing_design(config, "uam_direct2cad", minio_bucket)
        else:
            print(
                "Please provide the name of a configuration file for the randomized run (yaml)")
    elif args.design == "newaxe-cargo":
        create_new_axe_cargo()
    elif args.design == "testquad-cargo":
        create_test_quad_cargo()
    elif args.design == "pickaxe":
        create_pick_axe()
    elif args.design == "superquad":
        create_super_quad()
    elif args.design == "inline-uav":
        create_inline_uav()
    elif args.design == "uno-inline-uav":
        create_uno_inline_uav()
    elif args.design == "tiltie":
        create_tiltie()
    else:
        raise ValueError("unknown design")


if __name__ == '__main__':
    print("Starting Architect")
    run()
