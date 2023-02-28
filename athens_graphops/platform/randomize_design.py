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

import random
from ..designer import Designer, StudyParam
from . import load_config_file


def create_random_design(configfile: str):
    return randomization_platform("Random", configfile)


def randomization_platform(variant: str, configfile: str):
    """
    Given an existing design graph (in Janusgraph), randomize parameters 
    that are defined in a yaml file.

    At this point, it is expected that the config yaml files are located 
    in the athens_graphops/platform/configs folder. There is an example of the 
    format - default_study_params.yaml. 
    This run uses only the uam_direct2cad workflow.
    
    If you want to run an existing design (in graphDB already) multiple times with 
    same values, use the configuration files created when the design was created. 
    These files have the min/max at the same value.
    """
    design_name, description, corpus_type, num_samples, study_params = load_config_file(configfile)

    # Adjust the structural parameters to select a random value between min/max value provided
    # in the configuration file.  Keep values rounded up to get integers.
    for val in study_params:
        if val.param_type == "Structural":
            rand_param = []
            for n in range(num_samples):
                max_value = min_value = 0
                for i in range(len(val.value)):
                    for key, value in val.value[i].items():
                        if key == "max":
                            max_value = value
                        elif key == "min":
                            min_value = value
                        else:
                            raise ValueError(
                                f"Structural parameter should only have max/min in configuration file,"
                                f"Entry {val.value[i]} was found."
                            )
                
                rand_param.append(round(random.uniform(min_value, max_value)))
            val.value = rand_param
  
    return design_name, description, corpus_type, study_params, num_samples