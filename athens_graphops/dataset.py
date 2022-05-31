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

from typing import Any, Dict, List

import json
import os
import random

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def load_json(filename: str) -> Any:
    try:
        with open(os.path.join(DATA_DIR, filename), 'r') as file:
            return json.load(file)
    except:
        return []


CORPUS_DATA = load_json('corpus_data.json')
CORPUS_SCHEMA = load_json('corpus_schema.json')
NACA_DATA = load_json('aero_info.json')


def get_model_data(model: str) -> Dict[str, Any]:
    for data in CORPUS_DATA:
        if data["model"] == model:
            return data
    else:
        raise ValueError("unknown model name " + model)


def property_table(classification: str) -> List[Dict[str, Any]]:
    result = []
    for mod in CORPUS_DATA:
        if mod["class"] != classification:
            continue

        entry = dict(mod["properties"])
        assert "MODEL" not in entry or entry["MODEL"] == mod["model"]
        entry["MODEL"] = mod["model"]
        result.append(entry)
    return result


BATTERY_TABLE = property_table("Battery")
MOTOR_TABLE = property_table("Motor")
PROPELLER_TABLE = property_table("Propeller")


def get_component_parameters(classification: str, model: str) -> List[str]:
    """
    Return the parameter list for the component specified
    """
    result = []
    for mod in CORPUS_DATA:
        if (mod["class"] == classification) and (mod["model"] == model):
            entry = dict(mod["parameters"])
            result.append(entry)
            # print(mod["model"])
            break

    return result


def random_component_selection(classification: str) -> str:
    """
    Return a randomly selected model name give a component classification
    """
    if classification == "Battery":
        select_table = BATTERY_TABLE
    elif classification == "Motor":
        select_table = MOTOR_TABLE
    elif classification == "Propeller":
        select_table = PROPELLER_TABLE
    else:
        print("Only classifications available for random selection are Battery, Motor and Propeller")

    assert select_table
    selected_component = random.choice(select_table)

    # print(selected_component)

    return selected_component["MODEL"]


def randomize_parameters(component_params: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Randomize the parameter values.  If no maximum is specified, arbritarily 
    create one by using a multiplication factor (max_multiply_factor).

    When no minimum is provided, the maximum is also absent. So, set min/max
    to assigned value, except when the parameter is "LENGTH". For this case,
    set minimum to 1 and maximum to max_multiply_factor * assigned.  Here are 
    the current cases where only "assigned" value is provided.
        * BatteryController: BOTTOM_CONN_DISP, TOP_CONN_DISP
        * Cylinder: LENGTH  (assigned value seems to be the maximum possible based on experimentation)
        * Motor: CONTROL_CHANNEL
        * NACA_Port_Connector: BOTTOM_CONNECTION_DISP
        * Wing: NACA_Profile
    """
    max_multiply_factor = 2
    for key in component_params[0]:
        # print(key)
        # print("Original Value: %s" % component_params[0][key]["assigned"])

        if 'minimum' not in component_params[0][key]:
            if key == "LENGTH":
                min_value = 1
                max_value = float(
                    component_params[0][key]["assigned"])
            else:
                min_value = float(component_params[0][key]["assigned"])
                max_value = float(component_params[0][key]["assigned"])
        else:
            min_value = float(component_params[0][key]["minimum"])
            if 'maximum' in component_params[0][key]:
                max_value = float(component_params[0][key]["maximum"])
            else:
                max_value = float(
                    component_params[0][key]["assigned"]) * max_multiply_factor

        # Note that some component parameters have a "minimum" value of 1, yet the
        # assigned is 0.  So the max value in this case will be 0.
        if (max_value == 0 and (min_value > max_value)):
            rand_param = float(component_params[0][key]["assigned"])
        else:
            rand_param = float(random.uniform(min_value, max_value))

        # print("Random value: %d" % rand_param)
        component_params[0][key]["assigned"] = str(rand_param)

    return component_params


def random_naca_profile_selection() -> str:
    """
    From the SwRI provided aero_info.json file, select a random NACA profile and return the
    number portion of the "Name".
    """
    naca_data_keys = [*NACA_DATA]
    # print(naca_data_keys)
    random_naca_profile = random.choice(naca_data_keys)

    return random_naca_profile[5:]


def get_corpus_assigned_parameters(component_params: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Return the assigned parameters from the corpus data (i.e. the component_params untouched)
    This is used for components that are currently not being randomized (minimizes code change 
    in architect.py).  Needed as we determine what combinations of components can be randomized.
    """
    return component_params


def randomize_cyl_length(component_params: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Randomize the LENGTH parameter only, all other parameters are set to the "assigned value".  
    This is being used in as experiments are done to determine how many (and what combination) 
    components can have randomized parameters.  Length of cylinders is the first step.
    
    Note: The length parameter only has an assigned value, based on experimentation this seems 
    to be the maximum value possible.
    """
    max_multiply_factor = 1
    for key in component_params[0]:
 
        if key == "LENGTH":
            min_value = 1
            max_value = float(
                component_params[0][key]["assigned"]) * max_multiply_factor

            component_params[0][key]["assigned"] = str(float(random.uniform(min_value, max_value)))

    return component_params
    

def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--property-table', metavar='CLS',
                        help="prints out the property table")
    args = parser.parse_args(args)

    if args.property_table:
        data = property_table(args.property_table)
        print(json.dumps(data, indent=2, sort_keys=True))


if __name__ == '__main__':
    run()
