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


def validate_corpus_data():
    counts = {cls: 0 for cls in CORPUS_SCHEMA.keys()}
    for mod in CORPUS_DATA:
        if mod["class"] not in CORPUS_SCHEMA:
            print("WARNING: unknown component class {}".format(mod["class"]))
            continue

        counts[mod["class"]] += 1
        cls = CORPUS_SCHEMA[mod["class"]]

        for key, val1 in cls["properties"].items():
            assert key in mod["properties"], "property {} is missing in {}".format(
                key, mod["name"])
            val2 = mod["properties"][key]
            if val1 == "float":
                float(val2)
            else:
                assert val1 == "str"

        for key, val1 in cls["parameters"].items():
            if key not in mod["parameters"]:
                print("WARNING: parameter {} is missing in {}".format(
                    key, mod["model"]))
                continue

            assert val1 in ["float", "int", "str"]

            for val2 in mod["parameters"][key].values():
                if val1 == "float":
                    float(val2)
                elif val1 == "int":
                    int(val2)

        for key in cls["connectors"]:
            assert key in mod["connectors"], "connector {} is missing in {}".format(
                key, mod["name"])

    print("Number of component types:")
    for key, val in counts.items():
        print("  {:30}{}".format(key, val))


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
    client.assign_parameter(design_name, 'TestInstance', 'CHORD_1', 'PARAM_CHORD_1')
    client.assign_parameter(design_name, 'TestInstance', 'CHORD_2', 'PARAM_CHORD_2')
    client.assign_parameter(design_name, 'TestInstance', 'MOUNT_SIDE', 'PARAM_MOUNT_SIDE')

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


def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--corpus-data', action='store_true',
                        help="validates the corpus against the schema")
    parser.add_argument('--create-instances', action='store_true',
                        help="creates a simple design for each model")
    args = parser.parse_args(args)

    if args.corpus_data:
        validate_corpus_data()

    if args.create_instances:
        validate_create_instances()


if __name__ == '__main__':
    run()
