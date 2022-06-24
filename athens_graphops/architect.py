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


def create_minimal():
    designer = Designer()
    designer.create_design("Minimal")
    designer.add_fuselage(name="fuselage",
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


def create_tail_sitter():
    designer = Designer()

    if False:
        designer.create_design("TailSitter3NarrowBody")

        fuselage = designer.add_fuselage(name="fuselage",
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
        designer.create_design("TailSitter3JoyRide")

        fuselage = designer.add_fuselage(name="fuselage",
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

    right_wing = designer.add_wing(name="right_wing",
                                   naca=wing_naca,
                                   chord=wing_chord,
                                   span=wing_span,
                                   load=wing_load,
                                   left_inst=fuselage,
                                   left_conn="RIGHT_CONNECTOR")

    left_wing = designer.add_wing(name="left_wing",
                                  naca=wing_naca,
                                  chord=wing_chord,
                                  span=wing_span,
                                  load=wing_load,
                                  right_inst=fuselage,
                                  right_conn="LEFT_CONNECTOR")

    battery_controller = designer.add_battery_controller("battery_controller")

    designer.add_battery(battery_model,
                         name="right_battery",
                         naca=wing_naca,
                         chord=wing_chord,
                         span=wing_span,
                         mount_side=1,
                         voltage_request=battery_voltage,
                         volume_percent=battery_percent,
                         wing_inst=right_wing,
                         controller_inst=battery_controller)

    designer.add_battery(battery_model,
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

        designer.add_wing(name="right_stear_wing",
                          naca=stear_wing_naca,
                          chord=stear_wing_chord,
                          span=stear_wing_span,
                          load=stear_wing_load,
                          left_inst=stear_bar2,
                          left_conn="RIGHT_CONNECTOR")

        designer.add_wing(name="left_stear_wing",
                          naca=stear_wing_naca,
                          chord=stear_wing_chord,
                          span=stear_wing_span,
                          load=stear_wing_load,
                          left_inst=stear_bar2,
                          left_conn="TOP_CONNECTOR")

    designer.set_config_param("Requested_Lateral_Speed_1", 50)
    designer.set_config_param("Requested_Lateral_Speed_3", 32)
    designer.set_config_param("Requested_Lateral_Speed_5", 46)
    designer.set_config_param("Q_Position_5", 0.01)
    designer.set_config_param("Q_Velocity_5", 0.1)
    designer.set_config_param("Q_Angles_5", 1.0)
    designer.set_config_param("Q_Angular_Velocity_5", 0.1)
    designer.set_config_param("R_5", 0.1)

    designer.close_design()


def create_vudoo():
    designer = Designer()
    designer.create_design("VUdoo5")

    fuselage = designer.add_fuselage(name="fuselage",
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

    right_wing = designer.add_wing(name="right_wing",
                                   naca=wing_naca,
                                   chord=wing_chord,
                                   span=wing_span,
                                   load=wing_load,
                                   left_inst=fuselage,
                                   left_conn="RIGHT_CONNECTOR")

    left_wing = designer.add_wing(name="left_wing",
                                  naca=wing_naca,
                                  chord=wing_chord,
                                  span=wing_span,
                                  load=wing_load,
                                  right_inst=fuselage,
                                  right_conn="LEFT_CONNECTOR")

    designer.add_battery(battery_model,
                         name="right_battery",
                         naca=wing_naca,
                         chord=wing_chord,
                         span=wing_span,
                         mount_side=1,
                         voltage_request=battery_voltage,
                         volume_percent=battery_percent,
                         wing_inst=right_wing,
                         controller_inst=battery_controller)

    designer.add_battery(battery_model,
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

        designer.add_wing(name="right_stear_wing",
                          naca=stear_wing_naca,
                          chord=stear_wing_chord,
                          span=stear_wing_span,
                          load=stear_wing_load,
                          left_inst=stear_bar2,
                          left_conn="RIGHT_CONNECTOR")

        designer.add_wing(name="left_stear_wing",
                          naca=stear_wing_naca,
                          chord=stear_wing_chord,
                          span=stear_wing_span,
                          load=stear_wing_load,
                          left_inst=stear_bar2,
                          left_conn="TOP_CONNECTOR")

    designer.close_design()


def create_vari_vudoo(num_designs: int, design_name: str, workflow: str):
    """
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

        # Note: There are two fuselages, with differing parameter names
        # Current designer.add_fuselage is for the "FUSE_SPHERE_CYL_CONE" version,
        # not the NACA_Fuse. This can be randomized in the future when
        # designer.add_fuselage is made more generic. For now, assuming only
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

        fuselage = designer.add_fuselage(name="fuselage",
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
        max_num_prop_sets = 16
        num_prop_sets = round(random.uniform(0, max_num_prop_sets))
        prop_set_config = ["Front", "Rear", "All", "None"]
        print("Number of Propeller/Motor sets: %d" % num_prop_sets)

        # Randomize stear wing parameters
        has_stear_wing = bool(random.getrandbits(1))
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
            stear_bar1_length = round(
                float(rand_bar_params["LENGTH"]["assigned"]))
            # Angle was set to 45 degrees in original design, randomizing here
            stear_bar2_front_angle = round(
                float(rand_bar_params["FRONT_ANGLE"]["assigned"]))
            valid_cylinder = 8 <= port_thickness < cylinder_diameter <= stear_bar1_length
            if valid_cylinder:
                print("Stear Bar 1: Valid length found (%f)" %
                      stear_bar1_length)
            else:
                print("Stear Bar 1: Invalid length (%f). Try again" %
                      stear_bar1_length)

        # print("Stear Bar Length1, Front Angle2: %f, %f" % (stear_bar1_length, stear_bar2_front_angle))

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

        right_wing = designer.add_wing(name="right_wing",
                                       naca=wing_naca,
                                       chord=wing_chord,
                                       span=wing_span,
                                       load=wing_load,
                                       left_inst=fuselage,
                                       left_conn="RIGHT_CONNECTOR")

        left_wing = designer.add_wing(name="left_wing",
                                      naca=wing_naca,
                                      chord=wing_chord,
                                      span=wing_span,
                                      load=wing_load,
                                      right_inst=fuselage,
                                      right_conn="LEFT_CONNECTOR")

        designer.add_battery(battery_model,
                             name="right_battery",
                             naca=wing_naca,
                             chord=wing_chord,
                             span=wing_span,
                             mount_side=1,
                             voltage_request=battery_voltage,
                             volume_percent=battery_percent,
                             wing_inst=right_wing,
                             controller_inst=battery_controller)

        designer.add_battery(battery_model,
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

                stear_bar2 = designer.add_cylinder(name="stear_bar2",
                                                   length=stear_wing_chord,
                                                   diameter=cylinder_diameter,
                                                   port_thickness=port_thickness,
                                                   front_angle=stear_bar2_front_angle,
                                                   mount_inst=stear_bar1,
                                                   mount_conn="REAR_CONNECTOR")

                designer.add_wing(name="right_stear_wing",
                                  naca=stear_wing_naca,
                                  chord=stear_wing_chord,
                                  span=stear_wing_span,
                                  load=stear_wing_load,
                                  left_inst=stear_bar2,
                                  left_conn="RIGHT_CONNECTOR")

                designer.add_wing(name="left_stear_wing",
                                  naca=stear_wing_naca,
                                  chord=stear_wing_chord,
                                  span=stear_wing_span,
                                  load=stear_wing_load,
                                  left_inst=stear_bar2,
                                  left_conn="TOP_CONNECTOR")

        designer.close_design()

        # For direct2cad, need to start creoson
        # if workflow == "uam_direct2cad":
        #    print("Starting CREO - architect")
        #    architecture.start_creo()

        # Run UAM_Workflow on the newly created design
        architecture.update_parameters("graphGUID", design_name_inst)
        # print(architecture.jenkins_parameters)
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
        if workflow == "uam_direct2cad":
            architecture.jenkins_client.grab_extra_jsons_direct2cad(
                design_name_inst)
            # In between runs, creoson should be stopped and started again, so stopping here
            # architecture.stop_creoson()

        # Consider removing design after each run
        architecture.client.delete_design(design_name_inst)
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
        "vari-vudoo"
    ])
    parser.add_argument('--variable-design-name', type=str,
                        help="indicates base design name when create multiple designs with randomized parameters")
    parser.add_argument('--num-designs', type=int,
                        help="indicates number of designs to create")
    # Currently only used with vari-vudoo
    parser.add_argument('--workbench', choices=["UAM_Workflows", "uam_direct2cad"],
                        help="indicates which workflow to run when creating designs")

    args = parser.parse_args(args)

    # Default workflow
    aWorkflow = "UAM_Workflows"
    if args.workbench:
        aWorkflow = args.workbench

    if args.design == "minimal":
        create_minimal()
    elif args.design == "tail-sitter":
        create_tail_sitter()
    elif args.design == "vudoo":
        create_vudoo()
    elif args.design == "vari-vudoo":
        if args.variable_design_name and args.num_designs:
            name = args.variable_design_name
            number_designs = args.num_designs
            create_vari_vudoo(number_designs, name, aWorkflow)
        else:
            print(
                "Please indicate the base design name (--variable-design-name) and number of designs (--num-designs")
    else:
        raise ValueError("unknown design")


if __name__ == '__main__':
    print("Starting Architect")
    run()
