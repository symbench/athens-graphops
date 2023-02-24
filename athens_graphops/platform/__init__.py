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
# Create sets of designs, where similar designs are grouped into a platform
# with variations indicated by parameters passed to the <name>_platform function


import importlib
import pkgutil
import inspect
import time
import yaml
import os
from csv import DictWriter
from collections.abc import Sequence
from itertools import chain
from typing import Any, Dict, List, Optional
from ..workflow import JenkinsClient
from ..query import Client
from .. import CONFIG
from ..designer import StudyParam


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

def write_study_params(design_name: str, params: Dict):
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

def align_study_params(params: List[StudyParam]):
    """
    Align the study parameters to the same number of runs.
    This allows having single values and lists of parameter values.
    All study_params entries should be StudyParm class.
    CargoMass (if available) could have one or two values and should be 
        applied across all sets of FDM parameters (if a list).
    For randomized designs, the structural parameters will have a list of values
        to represent each desired design sample (i.e. if the configuration file
        indicated 5 samples desired, each parameter will have a list of 5 randomized
        values).  Each design same should be tested across the set of FDM parameters
        and the CargoMass values.
    """
    # Create dictionaries of study parameters separated by param_type
    n_cargo = 0
    fdm_params = {}
    structural_params = {}
    for val in params:
        if isinstance(val, StudyParam):
            if val.param_type == "CargoMass":
                cargo_values = val.value
                n_cargo = len(cargo_values)
            elif val.param_type == "FDM":
                fdm_params[val.name] = val.value
            elif val.param_type == "Structural":
                structural_params[val.name] = val.value
        else:
            raise ValueError(
                f"Parameter {val.name} is not a StudyParam, "
                f"only StudyParam entries are allow."
            )

    # Determine the number of:
    # 1) FDM Studies - Maximum size list within the FDM type parameters
    # 2) FDM sets - How many times to repeat the FDM studies values 
    # 3) Design Studies - Randomized design sets for structural parameters
    n_fdm_studies = [len(v) for v in fdm_params.values() if isinstance(v, Sequence)]
    if n_fdm_studies:
        n_fdm_studies = max(n_fdm_studies)
    else:
        n_fdm_studies = 1
        
    if n_cargo == 0:
        fdm_sets = 1
    else:
        fdm_sets = n_cargo

    n_design_studies = [len(v) for v in structural_params.values() if isinstance(v, Sequence)]
    if n_design_studies:
        n_design_studies = max(n_design_studies)
    else:
        n_design_studies = 1

    # Flatten to create an entry for each Jenkins run
    # To minimize the Creo parameter updates in randomized designs, all 
    # FDM parameter sets will be run for a structural design before moving
    # to the next structural design set.  If cargo is involved, it will also
    # be varied before changing the structural design parameters.
    aligned_params = {}
    if n_cargo != 0:
        cargo_value_set = ([cargo_values[0]] * n_fdm_studies + [cargo_values[1]] * n_fdm_studies) * n_design_studies
        aligned_params["CargoMass"] = cargo_value_set

    for fdm_name in fdm_params:
        if isinstance(fdm_params[fdm_name], Sequence):
            if len(fdm_params[fdm_name]) != n_fdm_studies:
                raise ValueError(
                    f"Parameter {fdm_name} has {len(fdm_params[fdm_name])} values, "
                    f"but {n_fdm_studies} values are expected."
                )
            
            fdm_params_set = fdm_params[fdm_name] * (fdm_sets * n_design_studies)
        else:
            fdm_params_set = [fdm_params[fdm_name]] * (n_fdm_studies * fdm_sets * n_design_studies)

        aligned_params[fdm_name] = fdm_params_set

    for struct_name in structural_params:
        values = structural_params[struct_name]
        structural_params_set = []
        for i in range(len(values)):
            for j in range(fdm_sets * n_fdm_studies):
                structural_params_set.append(values[i])

    return aligned_params

def create_design_config(design_name: str, description: str, corpus_type: str, num_samples: int, params: List[StudyParam]):
    """Write design/study parameter information into a yaml file to allow randomization of the study parameters."""

    config_filename = f"{design_name}_config.yaml"
    configs_dir = os.path.join(os.path.dirname(__file__), 'configs')
    filename = os.path.join(configs_dir, config_filename)

    config_file_dict = {"design_name": design_name,
                        "description": description,
                        "corpus_type": corpus_type,
                        "num_samples": num_samples,
                        "fdm": None,
                        "params": None
    }

    fdm_params = []
    struct_params = []
    for val in params:
        if isinstance(val, StudyParam):
            if val.param_type == "CargoMass":
                config_file_dict["cargo_mass"] = val.value
            elif val.param_type == "FDM":
                fdm_params.append({val.name: val.value})
            elif val.param_type == "Structural":
                struct_params.append({val.name: [{"max": val.value}, {"min": val.value}]})

            config_file_dict["fdm"] =  fdm_params
            config_file_dict["params"] = struct_params
        else:
            raise ValueError(
                f"Parameter {val.name} is not a StudyParam, "
                f"only StudyParam entries are allow."
            )

    with open(filename, 'w') as config_file:
        yaml.safe_dump(config_file_dict, config_file, sort_keys=False)

    print(f"Design configuration written to {config_filename}.")
    return config_filename

def load_config_file(config_filename: str):
    """ 
    Load a yaml file defining information needed to create the study_params.cvs file and store 
    in self.study_params_list.
    """
    configs_dir = os.path.join(os.path.dirname(__file__), 'configs')

    filename = os.path.join(configs_dir, config_filename)
    if os.path.exists(filename):
        print("Reading {}".format(filename))
        with open(filename) as ymlfile:
            config_params = yaml.safe_load(ymlfile)
    else:
        raise ValueError(
            "Design Configuration file {} does not exist".format(filename))

    # Information desired back to calling routine:
    # 1) design_name
    # 2) description
    # 3) corpus_type
    # 4) num_samples
    # 5) list of StudyParams (combine "cargo_mass", "fdm" and "params" with types indicated)
    design_name = config_params["design_name"]
    description = config_params["description"]
    corpus_type = config_params["corpus_type"]
    num_samples = config_params["num_samples"]
    params_list = []
    if corpus_type == "UAV":
        if "cargo_mass" in config_params.keys():
            params_list.append(StudyParam("CargoMass", config_params["cargo_mass"], "CargoMass"))
        else:
            raise ValueError(
                "This is a UAV design and requires an entry for 'cargo_mass' in {}".format(filename))
    
    for entry in config_params["fdm"]:
        for key, value in entry.items():
            params_list.append(StudyParam(key, value, "FDM"))

    for entry in config_params["params"]:
        for key, value in entry.items():
            params_list.append(StudyParam(key, value, "Structural"))

    return design_name, description, corpus_type, num_samples, params_list


def run_design(design_name, study_filename):
    """
    This will run the Jenkins uam_direct2cad workflow 
    for the design created.  The results will be
    retrieved and stored in the results folder of this
    repository.  A json file defining the design is added
    to the data.zip
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
    parser.add_argument("--configfile", type=str, metavar='configuration filename',
                        help="indicates the configuration filename to use for the random design")
    parser.add_argument(
        "-r", "--run", action="store_true", help="Run the design."
    )

    args = parser.parse_args(args)
    if args.design == "random_design":
        if args.configfile:
            design_name, description, corpus_type, study_params, num_samples = designs[args.design](args.configfile)
        else:
            raise ValueError("For random designs, a configuration file (yaml) must be specified (--configfile)")
    # All other designs
    else: 
        design_name, description, corpus_type, study_params = designs[args.design]()
        create_design_config(design_name, description, corpus_type, num_samples, study_params)
        num_samples = 1

    study_params = align_study_params(study_params)
    study_filename = write_study_params(design_name, study_params)

    if args.run:
        run_design(design_name, study_filename)


if __name__ == "__main__":
    run()
