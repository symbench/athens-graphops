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

#===============================================================================
# This function is intented to randomize any design that is loaded into 
# the JanusGraph database already.  The desired design must have a 
# configuration (YAML) file defined with the randomization parameters 
# and information to allow creation of a csv file


from ..designer import Designer, StudyParam


def create_random_design():
    return randomization_platform("Random")


def randomization_platform(variant):
    """
    Given an existing design graph (in Janusgraph), randomize parameters 
    that are defined in a yaml file.

    At this point, it is expected that the config yaml files are located 
    in the athens_graphops configs folder. There is an example of the 
    format - default_study_params.yaml. 
    MM TODO: Make flexible - This run uses the uam_direct2cad workflow.
    """
    #def randomize_existing_design(config_file: str, workflow: str, minio_bucket=''):
    # Setup Gremlin query and Jenkins interfaces
    #architecture = Architect()
    #architecture.open_jenkins_client(workflow)

    #if (minio_bucket != ''):
    #architecture.update_parameters("minioBucket", minio_bucket)
    #else:
    #minio_bucket = architecture.jenkins_parameters.get("minioBucket")

    # Convert yaml config file into csv file that indicates the parameter study desired.
    # The desired design name is in the config file, so it is returned for reference here.
    # MM TODO: use this from where it lands
    # design_name_inst = architecture.jenkins_client.create_direct2cad_csv(
    #                    minio_bucket, config_file)
    #print("Design Name to test: {}".format(design_name_inst))

    # Run UAM_Workflow on the yaml specified design
    """
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

    """
    pass