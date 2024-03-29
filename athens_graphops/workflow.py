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
            minio_host = CONFIG["miniohost"] + ":9000"
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

        #print("Server Address: %s" % self.jenkins_url)
        self.server = Jenkins(
            self.jenkins_url, auth=(username, password))
        print("User with username %s successfully logged in" % username)

        self.results_dir = os.path.join(os.path.dirname(__file__), 'results')
        self.configs_dir = os.path.join(os.path.dirname(__file__), 'configs')

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
        result = self.minio.fput_object(self.minio_bucket, study_filename, study_filename)
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
        retrieved_artifact = False
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
                    filename = f"{self.results_dir}\\{design_name}_data.zip"
                    print(filename)
                    with open(filename, "wb") as zip_artifact:
                        zip_artifact.write(artifacts_content)
                    retrieved_artifact = True
            else:
                print("No artifacts retrieved")
        else:
            print("Directory not available - %s" % self.results_dir)

        return retrieved_artifact

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
        print("Added design json file to data.zip information. Now available in the athens_graphops/results directory.")

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
