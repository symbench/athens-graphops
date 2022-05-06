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

from .dataset import CORPUS_DATA, CORPUS_SCHEMA
from .query import Client
from .designer import Designer
import json
import os
from typing import Any


def load_json(filename: str) -> Any:
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except:
        return []

def get_design_data(design_folder: str):
    """
    Given a data.zip from a Jenkins run for a design, read in the following files:
      - componentMap.json
      - connectionMap.json
      - parameterMap.json
    """
    design_comps = load_json(os.path.join(design_folder, 'componentMap.json'))
    design_connects = load_json(os.path.join(design_folder, 'connectionMap.json'))
    design_parms = load_json(os.path.join(design_folder, 'parameterMap.json'))
    return design_comps, design_connects, design_parms


def validate_corpus_data():
    counts = {cls: 0 for cls in CORPUS_SCHEMA.keys()}
    for model in CORPUS_DATA:
        if model["class"] not in CORPUS_SCHEMA:
            print("WARNING: unknown component class {}".format(model["class"]))
            continue

        counts[model["class"]] += 1
        model_class = CORPUS_SCHEMA[model["class"]]

        for prop_name, prop_type in model_class["properties"].items():
            assert prop_name in model["properties"], "property {} is missing in {}".format(
                prop_name, model["name"])
            prop_val = model["properties"][prop_name]
            if prop_type == "float":
                float(prop_val)
            else:
                assert prop_type == "str"

        for param_name, param_type in model_class["parameters"].items():
            if param_name not in model["parameters"]:
                print("WARNING: parameter {} is missing in {}".format(
                    param_name, model["model"]))
                continue

            assert param_type in ["float", "int", "str"]

            for param_val in model["parameters"][param_name].values():
                if param_type == "float":
                    float(param_val)
                elif param_type == "int":
                    int(param_val)

            if param_type in ["float", "int"]:
                minimum = float(model["parameters"][param_name].get(
                    "minimum", "-inf"))
                maximum = float(model["parameters"][param_name].get(
                    "maximum", "inf"))

                if minimum > maximum:
                    print("WARNING: invalid minimum {} and maximum {} values of parameter {} in {}".
                          format(minimum, maximum, param_name, model["model"]))

                assigned = model["parameters"][param_name].get("assigned")
                if assigned is not None:
                    assigned = float(assigned)

                    if assigned < minimum:
                        print("WARNING: invalid assigned {} and minimum {} values of parameter {} in {}".
                              format(assigned, minimum, param_name, model["model"]))

                    if assigned > maximum:
                        print("WARNING: invalid assigned and maximum values of parameter {} in {}".
                              format(assigned, maximum, param_name, model["model"]))

        for conn_name in model_class["connectors"]:
            assert conn_name in model["connectors"], "connector {} is missing in {}".format(
                conn_name, model["name"])

    print("Number of component types:")
    for prop_name, val in counts.items():
        print("  {:30}{}".format(prop_name, val))


def validate_create_instances():
    client = Client()

    # TODO: Go through all models in CORPUS_DATA and create a design with
    # a single instance with all/some parameters set to random values based
    # on parameter types (no need to observe the min/max), then verify that
    # the reloaded instance data matches what we expect. Do not assert, print
    # out errors

    print("Testing Tattu19AhLi")
    design_name = 'ValidationDesign'

    client.create_design(design_name)
    client.create_instance(design_name, 'Tattu19AhLi', 'TestInstance')
    client.create_parameter(design_name, 'PARAM_CHORD_1', 101.0)
    client.create_parameter(design_name, 'PARAM_CHORD_2', 102.0)
    client.create_parameter(design_name, 'PARAM_MOUNT_SIDE', 103)
    client.create_parameter(design_name, 'PARAM_SPAN', 114.0)
    client.assign_parameter(design_name, 'TestInstance',
                            'CHORD_1', 'PARAM_CHORD_1')
    client.assign_parameter(design_name, 'TestInstance',
                            'CHORD_2', 'PARAM_CHORD_2')
    client.assign_parameter(design_name, 'TestInstance',
                            'MOUNT_SIDE', 'PARAM_MOUNT_SIDE')

    design = client.get_design_data(design_name)

    assert len(design) == 1
    design = design[0]

    assert design['design'] == design_name
    assert len(design['connections']) == 0

    assert len(design['instances']) == 1
    instance = design['instances'][0]
    assert instance['model'] == 'Tattu19AhLi'
    assert instance['name'] == 'TestInstance'
    assert instance['assignment'] == {
        'CHORD_1': 'PARAM_CHORD_1',
        'CHORD_2': 'PARAM_CHORD_2',
        'MOUNT_SIDE': 'PARAM_MOUNT_SIDE',
    }

    assert design['parameters'] == {
        "PARAM_CHORD_1": "101.0",
        "PARAM_CHORD_2": "102.0",
        "PARAM_MOUNT_SIDE": "103",
        "PARAM_SPAN": "114.0"
    }

    client.close()


def create_many_cylinders():
    designer = Designer()
    designer.create_design("ManyCylinders")

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

    previous = designer.fuselage
    for diameter in [10, 20, 30, 50, 100, 150, 200]:
        for port_thickness in [8, 15, 25, 40, 80, 150]:
            if not port_thickness < diameter:
                continue
            for length in [20, 30, 50, 100, 200, 300, 400, 500]:
                if not diameter <= length:
                    continue

                instance = designer.add_cylinder(
                    name=designer.get_name(),
                    port_thickness=port_thickness,
                    diameter=diameter,
                    length=length)
                designer.connect(previous, "REAR_CONNECTOR",
                                 instance, "FRONT_CONNECTOR")
                previous = instance

    designer.close_design()


def create_all_motors():
    """
    TODO: create a design with cylinders attached at the back that
    hold all possible motors (from CORPUS_DATA).
    """
    
    designer = Designer()
    designer.create_design("AllMotors")

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

    # Determine the cylinder length by adding the CAN diameter widths of each motor 
    num_motors = 0
    cylinder_diameter = 30.0
    cylinder_thickness = 22.5
    length_pad = 0.2
    previous = designer.fuselage

    for model in CORPUS_DATA:
        if model["class"] == "Motor":
            num_motors += 1

            # Add a cylinder
            cylinder_length = float(model["properties"]["CAN_DIAMETER"]) + length_pad
            cylinder_name = "cyl_" + designer.get_name()
            cyl_instance = designer.add_cylinder(
                name=cylinder_name,
                port_thickness=cylinder_thickness,
                diameter=cylinder_diameter,
                length=cylinder_length)
            designer.connect(previous, "REAR_CONNECTOR",
                             cyl_instance, "FRONT_CONNECTOR")
            previous = cyl_instance

            # Add motor
            motor_name = "motor_" + designer.get_name()
            motor_instance = designer.add_motor(
                name=motor_name,  
                model=model["properties"]["MODEL"]            
            )
            designer.connect(cyl_instance, "TOP_CONNECTOR",
                            motor_instance, "Base_Connector")
 
    print("Number of Motors: %d" % num_motors)
    designer.close_design()


def validate_all_motors(design_folder: str):
    """
    Verify that all motors were added to the "create_all_motor" design by inspecting the data.zip output,
    specifically the "componentMap.json" file.  Not parameters are set for motors, so no additional testing
    is used.
    """
    val_comps, val_connects, val_params = get_design_data(design_folder)

    num_motors = 0
    design_num_motors = 0
    for model in CORPUS_DATA:
        if model["class"] == "Motor":
            num_motors += 1
            # Search for its existance in the design result being validated
            comp = list(filter(lambda x: (x["LIB_COMPONENT"] == model["properties"]["MODEL"]), val_comps))
            if not len(comp):
                print("%s motor is missing" % model["properties"]["MODEL"])
            else:
                design_num_motors += 1
    
    print("Test motors: %d, Design motors: %d" % (num_motors, design_num_motors))
    if num_motors == design_num_motors:
        print("SUCCESS: All motors made it into the design")
    else:
        print("FAILED: Missing motors listed above")


def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--corpus-data', action='store_true',
                        help="validates the corpus against the schema")
    parser.add_argument('--create-instances', action='store_true',
                        help="creates a simple design for each model")
    parser.add_argument('--create-many-cylinders', action='store_true',
                        help="creates a design with various cylinders")
    parser.add_argument('--create-all-motors', action='store_true',
                        help="creates a design with all motors attached")
    parser.add_argument('--validate-all-motors', action='store_true',
                        help="validate a design with all motors attached")
    parser.add_argument('--design-loc', type=str,
                        help="indicates location of validation design folder")
    args = parser.parse_args(args)

    if args.corpus_data:
        validate_corpus_data()
    if args.create_instances:
        validate_create_instances()
    if args.create_many_cylinders:
        create_many_cylinders()
    if args.create_all_motors:
        create_all_motors()
    if args.validate_all_motors:
        if args.design_loc:
            file_folder = args.design_loc
            validate_all_motors(file_folder)
        else:
            print("Please indicate the design folder with '--design-loc' argument")


if __name__ == '__main__':
    run()
