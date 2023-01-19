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
    design_connects = load_json(os.path.join(
        design_folder, 'connectionMap.json'))
    design_parms = load_json(os.path.join(design_folder, 'parameterMap.json'))
    return design_comps, design_connects, design_parms


# Used to check corpus_data against the corpus schema (check_type=corpus) or look for possible
#   missing information in the corpus schema that is available in the corpus data (check_type=schema)
def validate_corpus_data(check_type='corpus'):
    assert check_type in ["corpus", "schema"]
    counts = {cls: {'UAV': 0, 'UAM': 0, 'Both': 0}
              for cls in CORPUS_SCHEMA.keys()}
    ids = set()

    for model in CORPUS_DATA:
        if check_type == "corpus":
            if model["id"] in ids:
                print("ERROR: Multiple models with the same id {}".format(model["id"]))
            else:
                ids.add(model["id"])

        if model["class"] not in CORPUS_SCHEMA:
            print("WARNING: Unknown component class {}".format(model["class"]))
            continue

        # Parameters and properties may be different across corpus types (i.e. battery)
        # Create a flag on status of the information, if it is not available, it will be
        # caught in the next sections, so just not missing here
        # Temporarily, sensors does not indicate CORPUS
        if "CORPUS" in model["properties"].keys():
            if model["properties"]["CORPUS"]:
                model_corpus_prop = model["properties"]["CORPUS"]
            else:
                # Assumes UAM parts may not include the flag yet
                model_corpus_prop = "UAM"
            # If both are indicate, then they are the same so picked one for class definition (model_corpus_type)
            if model_corpus_prop == "Both" or model_corpus_prop == "BOTH":
                model_corpus_type = "UAM"
                # For the one component (Orient) that uses all caps
                if model_corpus_prop == "BOTH":
                    model_corpus_prop = "Both"
            else:
                model_corpus_type = model_corpus_prop

        counts[model["class"]][model_corpus_prop] += 1
        model_class = CORPUS_SCHEMA[model["class"]]
        if model["class"] == "Battery":
            model_class = model_class[model_corpus_type]
            #print("{} Battery schema used: {}".format(model["model"], model_class))

        # Make sure that all the schema class properties are defined in the corpus data model
        if check_type == "corpus":
            for prop_name, prop_type in model_class["properties"].items():
                if not (prop_name in model["properties"]):
                    print("ERROR: Property {} is missing in {} ({})".format(
                        prop_name, model["model"], model["class"]))
                # assert prop_name in model["properties"], "property {} is missing in {}".format(
                #    prop_name, model["model"])
                else:
                    prop_val = model["properties"][prop_name]
                    if prop_type == "float":
                        float(prop_val)
                    elif prop_type == "int":
                        int(prop_val)
                    else:
                        assert prop_type == "str"

        # See if corpus data model has any properties not defined in the schema
        if check_type == "schema":
            for prop_name_corpus, prop_val_corpus in model["properties"].items():
                if not (prop_name_corpus in model_class["properties"]):
                    print("WARNING: Property {} from {} ({}) is not defined in the corpus schema".format(
                        prop_name_corpus, model["model"], model["class"]))

        # Make sure that all the schema class parameters are defined in the corpus data model
        if check_type == "corpus":
            for param_name, param_type in model_class["parameters"].items():
                if param_name not in model["parameters"]:
                    print("ERROR: Parameter {} is missing in {} ({})".format(
                        param_name, model["model"], model["class"]))
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
                        print("WARNING: Invalid minimum {} and maximum {} values of parameter {} in {} ({})".
                              format(minimum, maximum, param_name, model["model"], model["class"]))

                    assigned = model["parameters"][param_name].get("assigned")
                    if assigned is not None:
                        assigned = float(assigned)

                        if assigned < minimum:
                            print("WARNING: Invalid assigned {} and minimum {} values of parameter {} in {} ({})".
                                  format(assigned, minimum, param_name, model["model"], model["class"]))

                        if assigned > maximum:
                            print("WARNING: Invalid assigned and maximum values of parameter {} in {} ({})".
                                  format(assigned, maximum, param_name, model["model"], model["class"]))

        # See if corpus data model has any properties not defined in the schema
        if check_type == "schema":
            for param_name_corpus, param_val_corpus in model["parameters"].items():
                if param_name_corpus not in model_class["parameters"]:
                    print("WARNING: Parameter {} from {} ({}) is not defined in the corpus schema".format(
                        param_name_corpus, model["model"], model["class"]))

        # Make sure that all the schema class parameters are defined in the corpus data model
        if check_type == "corpus":
            for conn_name in model_class["connectors"]:
                # assert conn_name in model["connectors"], "connector {} is missing in {}".format(
                #    conn_name, model["model"])
                if not (conn_name in model["connectors"]):
                    print("ERROR: Connector {} is missing in {} ({})".format(
                        conn_name, model["model"], model["class"]))

        # See if corpus data model has any properties not defined in the schema
        if check_type == "schema":
            for conn_name_corpus in model["connectors"]:
                if not (conn_name_corpus in model_class["connectors"]):
                    print("WARNING: Connector {} from {} ({}) is not defined in the corpus schema".format(
                        conn_name_corpus, model["model"], model["class"]))

    print("Number of component types:")
    print("  {:30} UAV{:5} UAM{:5} Both{:5}".format('', '', '', ''))
    for prop_name, val in counts.items():
        print("  {:30} {:5}  {:5}  {:5}".format(
            prop_name, val['UAV'], val['UAM'], val['Both']))


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

    designer.add_fuselage_uam(name="fuselage",
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
                    name=designer.generate_name(),
                    port_thickness=port_thickness,
                    diameter=diameter,
                    length=length)
                designer.connect(previous, "REAR_CONNECTOR",
                                 instance, "FRONT_CONNECTOR")
                previous = instance

    designer.close_design()


def create_all_motors():
    """
    Creates a design with cylinders attached at the back that
    hold all possible motors (from CORPUS_DATA).
    """

    designer = Designer()
    designer.create_design("AllMotors")

    designer.add_fuselage_uam(name="fuselage",
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
            cylinder_length = float(
                model["properties"]["CAN_DIAMETER"]) + length_pad
            cylinder_name = "cyl_" + designer.generate_name()
            cyl_instance = designer.add_cylinder(
                name=cylinder_name,
                port_thickness=cylinder_thickness,
                diameter=cylinder_diameter,
                length=cylinder_length)
            designer.connect(previous, "REAR_CONNECTOR",
                             cyl_instance, "FRONT_CONNECTOR")
            previous = cyl_instance

            # Add motor
            motor_name = "motor_" + designer.generate_name()
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
    Verify that all motors were added to the "create_all_motors" design by inspecting the data.zip output,
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
            comp = list(filter(lambda x: (
                x["LIB_COMPONENT"] == model["properties"]["MODEL"]), val_comps))
            if not len(comp):
                print("%s motor is missing" % model["properties"]["MODEL"])
            else:
                design_num_motors += 1

    print("Test motors: %d, Design motors: %d" %
          (num_motors, design_num_motors))
    if num_motors == design_num_motors:
        print("SUCCESS: All motors made it into the design")
    else:
        print("FAILED: Missing motors listed above")


def create_all_propellers():
    """
    Create a design with cylinders attached at the back that
    hold all possible propellers (from CORPUS_DATA).  To attach
    the proprellers, include a motor with the same "SHAFT_DIAMETER"
    as the propeller.  To handle the large number of propellers (940),
    there will be four designs created in the graph database.
    """
    # Create a list of motors with unique shaft diameters to use in attaching propellers.
    # Also, create a list of unique propeller shaft diameters.
    # Note: in the current (05/2022) UAM corpus, all propellers use the same
    # shaft size, but there are 11 different motor shaft sizes
    diff_shaft_motors = []
    unique_motors = []
    diff_shaft_props = []
    for model in CORPUS_DATA:
        if model["class"] == "Motor" and not diff_shaft_motors.count(model["properties"]["SHAFT_DIAMETER"]):
            diff_shaft_motors.append(model["properties"]["SHAFT_DIAMETER"])
            unique_motors.append(model)

        if model["class"] == "Propeller" and not diff_shaft_props.count(model["properties"]["SHAFT_DIAMETER"]):
            diff_shaft_props.append(model["properties"]["SHAFT_DIAMETER"])

    # For debugging
    # print(diff_shaft_motors)
    # print(len(diff_shaft_motors))
    # print(unique_motors)
    # print(len(unique_motors))
    # print(diff_shaft_props)
    # print(len(diff_shaft_props))

    num_designs = 4
    designer_names = []
    previous = []
    for x in range(num_designs):
        propdesign_name = "AllPropellers" + str(x)
        designer_names.append(Designer())
        designer_names[x].create_design(propdesign_name)

        designer_names[x].add_fuselage_uam(name="fuselage",
                                           length=2000,
                                           sphere_diameter=1520,
                                           middle_length=300,
                                           tail_diameter=200,
                                           floor_height=150,
                                           seat_1_fb=1000,
                                           seat_1_lr=-210,
                                           seat_2_fb=1000,
                                           seat_2_lr=210)
        previous.append(designer_names[x].fuselage)

    # Determine the cylinder length by adding the CAN diameter widths of each motor
    num_props = 0
    cylinder_diameter = 30.0
    cylinder_thickness = 22.5
    length_pad = 0.2

    current_designer = 0
    for model in CORPUS_DATA:
        if model["class"] == "Propeller":
            num_props += 1
            print("Designer Name: %s" %
                  designer_names[current_designer].design)

            # Select motor to use for design creation
            # that matches propeller shaft diameter
            for motor in unique_motors:
                if float(motor["properties"]["SHAFT_DIAMETER"]) == float(model["properties"]["SHAFT_DIAMETER"]):
                    #print("found motor")
                    motor_model = motor["properties"]["MODEL"]
                    motor_can_diameter = float(
                        motor["properties"]["CAN_DIAMETER"])
                    break

            # Add a cylinder
            cylinder_length = motor_can_diameter + length_pad
            cylinder_name = "cyl_" + \
                designer_names[current_designer].get_name()
            cyl_instance = designer_names[current_designer].add_cylinder(
                name=cylinder_name,
                port_thickness=cylinder_thickness,
                diameter=cylinder_diameter,
                length=cylinder_length)
            designer_names[current_designer].connect(previous[current_designer], "REAR_CONNECTOR",
                                                     cyl_instance, "FRONT_CONNECTOR")
            previous[current_designer] = cyl_instance

            # Add motor
            motor_name = "motor_" + designer_names[current_designer].get_name()
            motor_instance = designer_names[current_designer].add_motor(
                name=motor_name,
                model=motor_model
            )
            designer_names[current_designer].connect(cyl_instance, "TOP_CONNECTOR",
                                                     motor_instance, "Base_Connector")

            # Add propeller
            propeller_name = "prop_" + \
                designer_names[current_designer].get_name()
            propeller_instance = designer_names[current_designer].add_propeller(
                name=propeller_name,
                model=model["properties"]["MODEL"],
                prop_type=int(model["parameters"]["Prop_type"]["assigned"]),
                direction=int(model["parameters"]["Direction"]["assigned"])
            )
            designer_names[current_designer].connect(motor_instance, "Prop_Connector",
                                                     propeller_instance, "MOTOR_CONNECTOR_CS_IN")

            current_designer += 1
            if current_designer == num_designs:
                current_designer = 0

    print("Number of Propellers: %d" % num_props)
    for x in range(num_designs):
        designer_names[x].close_design()


def validate_all_propellers(design_folder: str):
    """
    Verify that all propellers were added to the "create_all_propellers" design by inspecting the data.zip output,
    specifically the "componentMap.json" file. Due to the number of propellers, multiple designs were created to
    include all the propellers.
    """
    # Find any sub folders with designs
    input_designs = []
    for file in os.listdir(design_folder):
        d = os.path.join(design_folder, file)
        if os.path.isdir(d):
            input_designs.append(d)
    # If no subfolders, then only one design is available
    if not input_designs:
        input_designs.append(design_folder)

    num_propellers = 0
    design_num_propellers = 0
    num_designs = len(input_designs)

    # Get the design information for all the designs
    design_comps = []
    design_connects = []
    design_params = []
    for x in range(num_designs):
        val_comps, val_connects, val_params = get_design_data(input_designs[x])
        design_comps.append(val_comps)
        design_connects.append(val_connects)
        design_params.append(val_params)

    # Look through all input designs to see if propellers are available and correct
    found = False
    for model in CORPUS_DATA:
        if model["class"] == "Propeller":
            num_propellers += 1
            # Search for its existance in the design result being validated
            for num in range(num_designs):
                comp = list(filter(lambda x: (
                    x["LIB_COMPONENT"] == model["properties"]["MODEL"]), design_comps[num]))
                if comp:
                    found = True
                    # print("%s propeller found in Design # %d" % (model["properties"]["MODEL"], num))
                    # Check if parameters are correct, get design from graph
                    # Need information in designParameter.json file (Prop_type and Direction) - ticket submitted
                    break
            if not found:
                print("%s propeller is missing" % model["properties"]["MODEL"])
            else:
                design_num_propellers += 1

    print("Test propellers: %d, Design propellers: %d" %
          (num_propellers, design_num_propellers))
    if num_propellers == design_num_propellers:
        print("SUCCESS: All propellers made it into the design")
    else:
        print("FAILED: Missing propellers listed above")


def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--corpus-data', choices=["corpus", "schema"],
                        help="validates the corpus against the schema (corpus) or schema against corpus (schema)")
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
    parser.add_argument('--create-all-propellers', action='store_true',
                        help="creates a design with all propellers attached")
    parser.add_argument('--validate-all-propellers', action='store_true',
                        help="validate a design with all propellers attached")

    args = parser.parse_args(args)

    if args.corpus_data:
        check_type = args.corpus_data
        validate_corpus_data(check_type)
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
    if args.create_all_propellers:
        create_all_propellers()
    if args.validate_all_propellers:
        if args.design_loc:
            file_folder = args.design_loc
            validate_all_propellers(file_folder)
        else:
            print("Please indicate the design folder with '--design-loc' argument")


if __name__ == '__main__':
    run()
