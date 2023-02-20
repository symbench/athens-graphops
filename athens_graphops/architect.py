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

    architecture.close_client()
    architecture.close_jenkins_client()


# >>>>>>>>MM TODO: the rest of this is example of creating a config YAML file - keep until refactored
# def create_tail_sitter(workflow: str, minio_name: str, num_samples: int):
    """
    This is for the UAM corpus
    """
    """
    # <<<<MM TODO: remove this function: architecture.set_fdm_parameters(design_fdm_parameters)

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
"""


def create_vari_vudoo(num_designs: int, design_name: str, workflow: str, minio_name: str, num_samples: int):
    """
    This is for the UAM corpus.
    Create a Vudoo based design, but the parameters are randomize to create
    a unique design each time. User should supply the number of designs
    desired and the base design name.  All designs will be added to the graph.
    The workflow is the Jenkins workflow that will be run on each design.
    """
    """
    # Setup Gremlin query and Jenkins interfaces
    architecture = Architect()
    architecture.open_jenkins_client(workflow)
    # if workflow == "uam_direct2cad":
    #    architecture.connect_creoson_server()

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
    """


def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('design', choices=[
        "random-existing"
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

    if args.design == "random-existing":
        if args.config_file:
            config = args.config_file
            # At this time (8/30/22), this option only works for uam_direct2cad workflow
            # Providing minio_bucket name is optional
            randomize_existing_design(config, "uam_direct2cad", minio_bucket)
        else:
            print(
                "Please provide the name of a configuration file for the randomized run (yaml)")
    else:
        raise ValueError("unknown design")


if __name__ == '__main__':
    print("Starting Architect")
    run()
