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
#
#
#===============================================================================
# JenkinsClient interacts with the SwRI Jenkins tools to run desired
# workflow with the indicated graph and parameters
#
# This class was borrowed from https://github.com/symbench/symbench-athens-client
# (by Umesh Timalsina)


from email import header
from typing import Any, Dict, List, Optional
import time
from . import CONFIG
import sys
import os
import json
import zipfile
import requests
import yaml
import random
import csv
import copy
from minio import Minio
from api4jenkins import Jenkins
from api4jenkins.exceptions import ItemNotFoundError
from .dataset import get_component_min_max
from .query import Client


# class JobFailedError(Exception):
#    """Error to be raised when a job fails."""


class JenkinsClient:
    """The client to the symbench athens server.
    Parameters
    ----------
    jenkins_url: str
        The url for the jenkins server
    username: str
        The username to login with
    password: str
        The password to login with
    minio_url: str
        The url for the Minio server
    minio_username: str
        The Minio username to login with
    minio_password: str
        The Minio username to login with
    minio_bucket: str
        The Minio bucket folder to use

    Attributes
    ----------
    server: api4jenkins.Jenkins
        The python interface for the jenkins server
    """

    def __init__(self,
                 jenkins_url: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 minio_host: Optional[str] = None,
                 minio_username: Optional[str] = None,
                 minio_password: Optional[str] = None,
                 minio_bucket: Optional[str] = None
                 ):
        if jenkins_url is None:
            self.jenkins_url = "http://" + CONFIG["hostname"] + ":8080"
        else:
            self.jenkins_url = jenkins_url

        if username is None:
            username = CONFIG["jenkinsuser"]
        if password is None:
            password = CONFIG["jenkinspwd"]
        if minio_host is None:
            minio_host = CONFIG["miniohost"]
        if minio_username is None:
            minio_username = CONFIG["miniouser"]
        if minio_password is None:
            minio_password = CONFIG["miniopwd"]
        if minio_bucket is None:
            self.minio_bucket = CONFIG["miniobucket"]
        else: 
            self.minio_bucket = minio_bucket

        self.minio = Minio(
            minio_host,
            access_key=minio_username,
            secret_key=minio_password,
            secure=False,
        )
        found = self.minio.bucket_exists(self.minio_bucket)
        if not found:
            print(f"Creating MinIO bucket {self.minio_bucket}")
            self.minio.make_bucket(self.minio_bucket)

        print("Server Address: %s" % jenkins_url)
        self.server = Jenkins(
            self.jenkins_url, auth=(username, password))
        print("User with username %s successfully logged in" % username)

        self.results_dir = os.path.join(os.path.dirname(__file__), 'results')
        self.configs_dir = os.path.join(os.path.dirname(__file__), 'configs')

        # MM TODO: look at this further when deciding what to do with the yaml file
        # Setup a dictionary to hold the information that will be save to or read in
        # from a yaml file which is used in the creation of the study_parameter.json file
        study_keys = ["description", "num_samples", "fdm", "params"]
        self.study_params_list = dict.fromkeys(study_keys, None)
        # MM TODO: Removing this - self.fdm_keys = ["Analysis_Type", "Flight_Path", "Requested_Lateral_Speed",
        #                 "Requested_Vertical_Speed", "Q_Position", "Q_Velocity", "Q_Angular_Velocity", "Q_Angles", "Ctrl_R"]

        # For parameter study csv files, it is assumed a design exists in the graph.
        # For development of a valid csv file, information from the yaml file indicating the
        # expected study setup will be validated against the indicated design in the graph.
        # So, setting up a query client here to allow access to the design graph information.
        self.client = None

    def open_query_client(self):
        """Open a query client (gremlin) to grab the graph design information"""
        assert self.client is None
        self.client = Client()

    def close_query_client(self):
        """Close a query client (gremlin) to grab the graph design information"""
        assert self.client is not None
        self.client.close()
        self.client = None

    def close(self):
        if self.server:
            sys.stderr.write("Deleted connection\n")
            self.server = None

        if self.client:
            assert self.client is not None
            print("Closing query client")
            self.client.close()
            self.client = None

    def get_user_info(self):
        """
        Return information for the currently logged in user.
        """
        user = self.server.user
        return {
            "fullName": user.full_name,
            "id": user.id,
            "description": user.description,
        }

    def get_available_jobs(self, names_only=False):
        """
        Returns available jobs from the server.
        Parameters
        ----------
        names_only: bool, default=False
            If true, return the job names only
        Returns
        -------
        list of dict or list of str
            The jobs available in the server
        """
        jobs = []
        for job in self.server.iter_jobs():
            jobs.append(job.full_name if names_only else job.api_json())
        return jobs

    def get_job_info(self, job_name):
        """
        Get information about the job and its builds
        """
        job = self.server.get_job(job_name)
        assert job, f"Provided job {job_name} doesn't exist"
        return job.api_json()

    def can_execute(self):
        """
        Return True if any worker nodes are connected
        """
        executor_nodes = list(
            filter(lambda node: node.name != "(master)", self.server.nodes)
        )

        return not all(node.offline for node in executor_nodes)

    def studyfile_to_minio(self, study_filename):
        """
        Copy the study CSV file to the Minio bucket setup by the default CONFIG
        or `--miniobucket` option on the command line
        """
        self.minio.fput_object(self.minio_bucket, study_filename, study_filename)
        print(f"Uploaded to MinIO {self.minio_bucket}/{study_filename}.")

    def build_and_wait(self, job_name, parameters):
        """
        Build a job and wait
        Parameters
        ----------
        job: str
            Name of the job
        parameters: dict
            Parameters for this build
        """
        job = self.server.get_job(job_name)
        if job is None:
            raise ItemNotFoundError(
                "Job with name %s doesn't exist" % job_name)

        # job.url is respose location, we need to override it
        job.url = self.jenkins_url + "/job/" + job_name + "/"
        item = job.build(**parameters)
        print("Job %s is waiting to be built" % job_name)

        while not item.get_build():
            time.sleep(1)

        print("Job %s is built" % job_name)

        build = item.get_build()
        print("Job %s is running. The build number is %d." %
              (job_name, build.number))
        print("\nThe build parameters are %s" % parameters)
        while not build.result:
            time.sleep(5)
            print("Still running the job %s" % job_name)
        print("Job %s is finished. The result is %s" %
              (job_name, build.result))
        if build.result != "SUCCESS":
            # For now, just mark the failure and go on
            # raise JobFailedError(
            #    "Job Failed. Please check the build parameters among others"
            # )
            print("Job %s FAILED, no data available" % job_name)
        return build

    def save_results_from_build(self, build, design_name: str):
        """
        Get results from a particular build as a data.zip and save in 
        results directory        
        """
        if os.path.isdir(self.results_dir):
            build_artifacts = build.api_json()["artifacts"]
            if len(build_artifacts):
                artifact_url = f'{build.url}artifact/{build_artifacts[0]["relativePath"]}'
                response = requests.get(
                    artifact_url,
                    auth=(CONFIG["jenkinsuser"], CONFIG["jenkinspwd"]),
                )
                if response.status_code != 200:
                    raise FileNotFoundError
                else:
                    print("Build artifacts retrieved")
                    artifacts_content = response.content
                    filename = f"{self.results_dir}/{design_name}_data.zip"
                    with open(filename, "wb") as zip_artifact:
                        zip_artifact.write(artifacts_content)
            else:
                print("No artifacts retrieved")
        else:
            print("Directory not available - %s" % self.results_dir)

    def add_design_json_to_results(self, design_name: str, design_json):
        """
        Add design json file to the results data.zip file for the specified 
        design
        """
        design_file = design_name + "_design_data.json"
        design_zip_file = design_name + "_data.zip"
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        # Save to a file in the results directory
        with open(os.path.join(self.results_dir, design_file), 'w') as file:
            json.dump(design_json[0], file)

        # Add file to data.zip for the design
        z = zipfile.ZipFile(os.path.join(
            self.results_dir, design_zip_file), "a")
        z.write(os.path.join(self.results_dir,
                design_file), arcname=design_file)
        z.close()

        # Remove design data file once it is inside the data.zip file
        os.remove(os.path.join(self.results_dir, design_file))
        print("Added design json file to data.zip information. Now available in the results directory.")

    def grab_extra_jsons_direct2cad(self, design_name: str):
        """
        The uam_direct2cad workflow has two common file (partMass.json and partLocs.json) that are
        currently not saved in results data.zip.  Grab these and add them to this zip file.
        """
        design_zip_file = design_name + "_data.zip"
        mass_file = "partMass.json"
        locs_file = "partLocs.json"
        workspace_dir = "C:/jwork/Agents/workspace/uam_direct2cad"

        if os.path.isfile(os.path.join(self.results_dir, design_zip_file)):
            z = zipfile.ZipFile(os.path.join(
                self.results_dir, design_zip_file), "a")

            if os.path.isfile(os.path.join(workspace_dir, mass_file)):
                z.write(os.path.join(workspace_dir,
                        mass_file), arcname=mass_file)
            else:
                print("No mass file exists")

            if os.path.isfile(os.path.join(workspace_dir, locs_file)):
                z.write(os.path.join(workspace_dir,
                        locs_file), arcname=locs_file)
            else:
                print("No location file exists")

            z.close()

        else:
            print("Design Result file (%s) not found" % design_zip_file)

    # MM TODO: redo the next 7 functions, consider moving the 
    def load_study_config(self, config_file: str):
        """ 
        Load a yaml file defining information needed to create the study_params.cvs file and store 
        in self.study_params_list.
        """
        filename = os.path.join(self.configs_dir, config_file)
        if os.path.exists(filename):
            print("Reading {}".format(filename))
            with open(filename) as ymlfile:
                self.study_params_list = yaml.safe_load(ymlfile)
        else:
            raise ValueError(
                "Study Parameter Configuration file {} does not exist".format(filename))

    def write_study_config(self, design_name: str):
        """
        Write a yaml file with the self.study_params_list configuration definition 
        """
        outfilename = os.path.join(
            self.configs_dir, design_name + "_study_params.yaml")

        #print("Before writing: {}".format(self.study_params_list))
        with open(outfilename, 'w') as file:
            yaml.dump(self.study_params_list, file)

    def build_study_dict(self, design_name: str, desc: str, fdm_params: List[Dict[str, Any]], comp_set_name: str, comp_class: str, comp_modelname: str, comp_names: List[str], param_name: str, num_samples=1, min_value=0.0, max_value=0.0):
        """
        Provide FDM params for the runs (flight_paths could be a list of paths) and components/parameter 
        information on what will be varied. Min/Max is optional, if not provided will be pulled from
        the corpus_data.json file. Randomization is indicated by indicating a 'num_samples' > 1.
        If more than one component/parameter is desired, a call to this function will be followed by the
        create_param_comp_entry function.        

        Note: Right now, only component parameters will be varied, but the yaml is setup to allow other
        variations as needed in the future.  

        * num_samples (optional)- when randomly sampling the parameter, how many samples are 
                                    desired, if not provided assume 1

        Information expected in fdm_params:
          * Analysis_Type - typically 3
          * Flight_Paths - current options are [1, 3, 4, 5]
          * Requested_Lateral_Speed
          * Requested_Vertical_Speed
          * Q_Position - value from 0-1
          * Q_Velocity - value from 0-1
          * Q_Angular_velocity - value from 0-1
          * Q_Angles - value from 0-1
          * Ctrl_R - value from 0-1

       Component parameter definition (comp_set_list: list of information provided from code building the graphs):
          * comp_set_name - this information is not translated into the yaml, but helps
                            define a set of components where the parameter value is shared 
          * comp_class - classification of components in this set (all should be the same classification) 
          * comp_modelname - component model name used by the comp_names instance (should be same for all listed)                                
          * parameter - name of parameter within identified component(s)
          * comp_names - list of component names in the graph for which the parameter is varied
          * max_value (optional)
          * min_value (optional)

          Note: if a specific value is desired, specify the same value for min/max information (defaults of 0.0/0.0 will use corpus data)
                (optionally indicate num_samples = 1)
        """
        print("Input Num_Samples: {}".format(num_samples))
        self.study_params_list['design_name'] = design_name
        self.study_params_list['description'] = desc
        self.study_params_list['fdm'] = fdm_params
        self.study_params_list['num_samples'] = num_samples

        self.create_param_comp_entry(
            comp_set_name, comp_class, comp_modelname, comp_names, param_name, min_value, max_value)

        print("Setup of study_params_list: {}".format(self.study_params_list))

    def create_param_comp_entry(self, comp_set_name: str, comp_class: str, comp_modelname: str, comp_names: List[str], param_name: str, min_value=0.0, max_value=0.0):
        """
        Create the component set entry for the yaml. Check for min/max/number sample definition.
        """
        # If min/max not provided, use the corpus data information to determine appropriate values
        if (min_value == 0.0) and (max_value == 0.0):
            min_value, max_value = get_component_min_max(
                comp_class, comp_modelname, param_name)

        comp_set_def = {comp_set_name: {"max": max_value,
                                        "min": min_value,
                                        "components": comp_names,
                                        "parameter": param_name}}
        if self.study_params_list['params'] == None:
            self.study_params_list['params'] = comp_set_def
        else:
            self.study_params_list['params'][comp_set_name] = comp_set_def[comp_set_name]

        #print("Current Param List: {}".format(self.study_params_list['params']))

    def duplicate_param_comp_entry(self, ref_comp_set_name: str, new_comp_set_name: str, new_param_name: str):
        """
        Create a duplicate parameter entry with different component set name.
        This is used when components have shared values for component parameters (such as CHORD_1 and CHORD_2 in wings)
        """
        params_dict = self.study_params_list['params']
        new_dict_entry = copy.deepcopy(params_dict[ref_comp_set_name])
        new_dict_entry['parameter'] = new_param_name
        self.study_params_list['params'][new_comp_set_name] = new_dict_entry
        print("New Entry in self.study_params_list: {}".format(
            self.study_params_list['params']))

    def build_param_change_list(self) -> List[Dict[str, Any]]:
        """
        From the yaml component set information, create a list of parameter requests that will be used
        to create each line of the csv file. Each item in the list will be a parameter and the associated
        random values for the desired number of samples (in dictionary form).  Min/max/num_samples to create
        desired number of component/param definition entries is found in the study_params_list populated by 
        a yaml file inputs.
        """
        self.open_query_client()
        parameter_csv_entry = dict()
        design_param_map = self.client.get_parameter_map(
            self.study_params_list['design_name'])
        print("design_param_map: {}".format(design_param_map))

        for comp_set_name in self.study_params_list['params']:
            print("comp_set_name={}".format(comp_set_name))
            comp_set_min = self.study_params_list['params'][comp_set_name]['min']
            comp_set_max = self.study_params_list['params'][comp_set_name]['max']
            #print("Min/Max: {}/{}".format(comp_set_min, comp_set_max))

            # Create random values for the parameter
            rand_values = []
            for x in range(self.study_params_list['num_samples']):
                rand_param = float(
                    round(random.uniform(comp_set_min, comp_set_max)))
                rand_values.append(rand_param)

            # Determine parameter names that will go into the header
            inst_names = self.study_params_list['params'][comp_set_name]['components']
            #print("Names: {}".format(inst_names))
            for inst_name in inst_names:
                print(inst_name)
                param_names = self.study_params_list['params'][comp_set_name]['parameter']
                if not isinstance(param_names, list):
                    param_list = [param_names]
                else:
                    param_list = param_names
                for param in param_list:
                    param_name = inst_name + "_" + param
                    # Check that component name/parameter is in the design
                    found = False
                    if len(design_param_map) == 0:
                        print(
                            "Query failed to provide the design parameter map to lookup the available parameters")
                    else:
                        for dict_entry in design_param_map:
                            if param_name in dict_entry.values():
                                #print("Found parameter: {}".format(param_name))
                                found = True
                                break
                    assert found, "{} not found in design parameter map".format(
                        param_name)

                    parameter_csv_entry[param_name] = rand_values

        self.close_query_client()
        return parameter_csv_entry

    def create_direct2cad_csv(self, minio_bucket: str, config_filename: str) -> str:
        """ 
        From the configuration file (yaml in configs folder), create a CSV file that sweeps the system parameters
        to run multiple configuration through direct2cad workflow.  Each line in the CSV represents a run of the FDM 
        and updates to system parameters.

        Return design name from configuration file to help with Jenkins run parameters.
        """
        # Load the configuration information into self.study_params_list
        self.load_study_config(config_filename)

        # Create list with FDM set (i.e. one line per flightpath) in sweep_config.  Each FDM parameter could
        # be a single value or a list.  If it is a list, it needs to be the same size as the number of 'flight_paths'.
        flat_flight_entries = dict.fromkeys(self.fdm_keys, None)
        i = 0
        for flight_path in self.study_params_list['fdm']['Flight_Path']:
            for key in self.fdm_keys:
                if type(self.study_params_list['fdm'][key]) == list:
                    value = self.study_params_list['fdm'][key][i]
                else:
                    value = self.study_params_list['fdm'][key]
                if flat_flight_entries[key] == None:
                    flat_flight_entries[key] = [value]
                else:
                    flat_flight_entries[key].append(value)
            i += 1

        #print("FDM params: {}".format(flat_flight_entries))

        # Get a list of parameter information that will be applied to each FDM array item for each component/parameter:
        param_change_entries = self.build_param_change_list()
        #print("Parameter change entries: {}".format(param_change_entries))
        print("Config information: {}".format(self.study_params_list))

        # Create a header for the csv file combining FDM and parameter information
        csv_file_entries = []
        header_line = []
        for key in self.fdm_keys:
            header_line.append(key)

        param_change_keys = param_change_entries.keys()
        header_line.extend(param_change_keys)
        # csv_file_entries.append(header_line)
        #print("CSV Header Line: {}".format(csv_file_entries))

        # Create combined list of FDM and parameter entries - each row will represent an cycle in the Jenkins run
        # Parameter dictionary has parameter names as keys and a list of values (size of number of samples)
        # So for each random number set, create the lines based on the number of flight path in the flat_flight_entries
        num_rand_values = len(list(param_change_entries.values())[0])
        #print("num_rand_value = {}".format(num_rand_values))
        for x in range(num_rand_values):
            param_value_line = []
            for param_entry in param_change_entries:
                param_value_list = param_change_entries[param_entry]
                param_value_line.append(str(param_value_list[x]))
            # FDM dictionary here has the parameter names as keys and a list of values (size of flight path specification)
            num_flight_paths = len(flat_flight_entries['Flight_Path'])
            #print("Num flight path = {}".format(num_flight_paths))
            for y in range(num_flight_paths):
                fdm_value_line = []
                for fdm_entry in flat_flight_entries:
                    fdm_value_line.append(
                        str(flat_flight_entries[fdm_entry][y]))
                csv_file_line = fdm_value_line + param_value_line
                #print("CSV File line: {}".format(csv_file_line))
                csv_file_entries.append(csv_file_line)

        #print("CSV file entries: {}".format(csv_file_entries))

        # Save results to csv file in minio bucket
        sweep_filename = config_filename.replace(".yaml", ".csv")
        sweep_file_dir = os.path.join(CONFIG["miniodir"], minio_bucket)
        run_sweep_param_file = os.path.join(sweep_file_dir, sweep_filename)
        with open(run_sweep_param_file, 'w', newline='') as file:
            csvfile_writer = csv.writer(file, delimiter=',')
            csvfile_writer.writerow(header_line)
            for entry in csv_file_entries:
                csvfile_writer.writerow(entry)

        print("Design CSV file written: {}".format(run_sweep_param_file))
        return self.study_params_list['design_name']


def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('workflow', choices=[
        "UAM_Workflows",
        "uam_direct2cad"])
    parser.add_argument('--design', type=str, metavar='design',
                        help="indicates the design name for a Jenkins workflow run")
    # Arguments for UAM_Workflows and UAV_Workflows
    parser.add_argument('--testname', choices=[
                        "/D_Testing/PET/FlightDyn_V2",
                        "/D_Testing/PET/FlightDyn_V2_AllPaths"],
                        help="indicates the test name for a Jenkins workflow run")
    parser.add_argument('--samples', type=str, metavar='samples',
                        help="indicates the number of samples for a Jenkins workflow run")
    parser.add_argument('--parameters', type=str, metavar='parameters',
                        help="indicates the design parameters for a Jenkins workflow run using parameter=value space separated string")
    # Arguments for uam_direct2cad
    parser.add_argument('--paramfile', type=str, metavar='inputname',
                        help="indicates the input file name for the parameter sweep (.csv)")
    parser.add_argument('--resultname', type=str, metavar='results',
                        help="indicates file name for the results of uam_direct2cad run (not currently used)")

    args = parser.parse_args(args)

    jenkins_url = "http://" + CONFIG["hostname"] + ":8080"
    jenkins_client = JenkinsClient(jenkins_url)

    # Default jenkins run parameters for UAM_Workflows
    if args.workflow == "UAM_Workflows":
        uam_run_parameters = {
            "graphGUID": "Rake",
            "PETName": "/D_Testing/PET/FlightDyn_V2_AllPaths",
            "NumSamples": "1",
            "DesignVars": '"Analysis_Type=3,3"'
        }
        if args.testname:
            if args.testname == "/D_Testing/PET/FlightDyn_V2" or args.testname == "/D_Testing/PET/FlightDyn_V2_AllPaths":
                uam_run_parameters["PETName"] = args.testname
            else:
                raise ValueError("unknown testname")
        if args.samples:
            uam_run_parameters["NumSamples"] = args.samples
        if args.parameters:
            uam_run_parameters["DesignVars"] = f'"{args.parameters}"'
        print(uam_run_parameters)

    elif args.workflow == "uam_direct2cad":
        uam_run_parameters = {
            "graphGUID": "Rake",
            "minioBucket": "graphops",
            "paramFile": "rand_design_runs.csv",
            "resultsFileName": "results123"
        }
        uam_run_parameters["minioBucket"] = CONFIG["miniobucket"]
        if args.paramfile:
            uam_run_parameters["paramFile"] = args.paramfile
        if args.resultname:
            uam_run_parameters["resultsFileName"] = args.resultname

    # Argument used in all runs
    if args.design:
        uam_run_parameters["graphGUID"] = args.design

    if (args.workflow == "UAM_Workflows") or (args.workflow == "uam_direct2cad"):
        jenkins_client.build_and_wait(
            job_name=args.workflow, parameters=uam_run_parameters)
        # get zip file
    else:
        raise ValueError("unknown workflow")

    jenkins_client.close()


if __name__ == '__main__':
    run()
