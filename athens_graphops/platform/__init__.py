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
import importlib
import pkgutil
import inspect
import time
from csv import DictWriter
from collections.abc import Sequence
from itertools import chain
from ..workflow import JenkinsClient
from ..query import Client
from .. import CONFIG


def __discover_designs():
    """Automatically discover and import all design creation functions."""
    designs = {}
    for mod_info in pkgutil.walk_packages(__path__, __name__ + "."):
        mod = importlib.import_module(mod_info.name)
        for name, func in inspect.getmembers(mod, inspect.isfunction):
            prefix = "create_"
            if name.startswith(prefix):
                designs[name[len(prefix):]] = func

    return designs

# MM TODO: consider moving these two functions to workflow
def write_study_params(design_name, params):
    """Write study parameters to a .csv file for use in Jenkins runs."""
    study_filename = f"{design_name}_study.csv"

    n_studies = len(next(iter(params.values())))
    with open(study_filename, "w", newline="") as study_file:
        writer = DictWriter(study_file, fieldnames=params.keys())
        writer.writeheader()
        for i in range(n_studies):
            writer.writerow({k: v[i] for k, v in params.items()})

    print(f"Study parameters written to {study_filename}.")
    return study_filename

def align_study_params(params):
    """Align the study parameters to the same number of runs.
    This allows to have single values and lists of parameter values.
    """

    n_studies = [len(v) for v in params.values() if isinstance(v, Sequence)]
    if n_studies:
        n_studies = max(n_studies)
    else:
        n_studies = 1

    aligned_params = {}
    for p_name in params:
        if isinstance(params[p_name], Sequence):
            if len(params[p_name]) != n_studies:
                raise ValueError(
                    f"Parameter {p_name} has {len(params[p_name])} values, "
                    f"but {n_studies} values are expected."
                )
            aligned_params[p_name] = params[p_name]
        else:
            aligned_params[p_name] = [params[p_name]] * n_studies

    return aligned_params

# MM TODO:  plan to remove this, keeping for now
def sweep_study_param(params, param_name, values):
    """Add or modify a parameter to sweep it in the study parameters."""
    aligned_params = align_study_params(params)
    n_studies = len(next(iter(aligned_params.values())))
    swept_params = {}
    swept_params[param_name] = list(chain(*([v] * n_studies for v in values)))
    for p_name in aligned_params:
        if p_name != param_name:
            swept_params[p_name] = list(
                chain(aligned_params[p_name] * len(values))
            )
    return swept_params


def run_design(design_name, study_filename):
    """
    This will run the Jenkins uam_direct2cad workflow 
    for the design created.  The results will be
    retrieved and stored in the results folder of this
    repository.  A json file defining the design is added
    to the data.zip information.
    """
    jenkins_client = JenkinsClient()
    query_client = Client()

    # Copy study parameter file to the minio location
    jenkins_client.studyfile_to_minio(study_filename)

    workflow = "uam_direct2cad"
    jenkins_parameters = {
        "graphGUID": design_name,
        "minioBucket": CONFIG["miniobucket"],
        "paramFile": study_filename,
        "resultsFileName": design_name
    }

    build = jenkins_client.build_and_wait(workflow, jenkins_parameters)
    # add time to allow Jenkins to make artifacts available
    time.sleep(10)
    artifacts_exist = jenkins_client.save_results_from_build(build, design_name)

    # Create json of all design information and add it to the Jenkins data.zip file
    if artifacts_exist:
        design_json = query_client.get_design_data(design_name)
        jenkins_client.add_design_json_to_results(design_name, design_json)

    query_client.close()


def run(args=None):
    import argparse

    designs = __discover_designs()
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "design",
        choices=designs.keys(),
    )
    parser.add_argument(
        "-r", "--run", action="store_true", help="Run the design."
    )

    args = parser.parse_args(args)
    design_name, study_params = designs[args.design]()
    study_params = align_study_params(study_params)
    study_filename = write_study_params(design_name, study_params)

    if args.run:
        run_design(design_name, study_filename)


if __name__ == "__main__":
    run()
