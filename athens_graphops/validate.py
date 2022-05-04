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
    pass


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
    args = parser.parse_args(args)

    if args.corpus_data:
        validate_corpus_data()
    if args.create_instances:
        validate_create_instances()
    if args.create_many_cylinders:
        create_many_cylinders()
    if args.create_all_motors:
        create_all_motors()


if __name__ == '__main__':
    run()
