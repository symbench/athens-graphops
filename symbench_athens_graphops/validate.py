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

from typing import Any, Dict, List, Optional

import json
import os

from . import CONFIG


def validate_corpus():
    with open(os.path.join(CONFIG["data_dir"], "better_corpus.json"), 'r') as file:
        corpus = json.load(file)
    with open(os.path.join(CONFIG["data_dir"], "corpus_schema.json"), 'r') as file:
        schema = json.load(file)

    counts = {cls: 0 for cls in schema.keys()}
    counts["Unknown"] = 0
    for typ in corpus:
        if typ["type"] not in schema:
            counts["Unknown"] += 1

        counts[typ["type"]] += 1
        cls = schema[typ["type"]]

        for key, val1 in cls["properties"].items():
            assert key in typ["properties"], "property {} is missing in {}".format(
                key, typ["name"])
            val2 = typ["properties"][key]
            if val1 == "float":
                float(val2)
            else:
                assert val1 == "str", "invalid value type in {}".format(
                    typ["properties"])

        for key, val1 in cls["parameters"].items():
            assert key in typ["parameters"],  "parameter {} is missing in {}".format(
                key, typ["name"])
            
            parameter_values = typ["parameters"][key]
            if "[]AssignedValue" in parameter_values:
                val2 = parameter_values["[]AssignedValue"]
            else:
                val2 = parameter_values["[]Default"]
            
            if val1 == "float":
                float(val2)
            elif val1 == "int":
                int(val2)
            else:
                assert val1 == "str", "invalid value type in {}".format( 
                    typ["parameters"]) 


        for key in cls["connectors"]:
            assert key in typ["connectors"], "connector {} is missing in {}".format(
                key, typ["name"])

    print("Number of component types:")
    for key, val in counts.items():
        print("  {:30}{}".format(key, val))


def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--corpus', action='store_true',
                        help="validates the corpus against the schema")
    args = parser.parse_args(args)

    if args.corpus:
        validate_corpus()


if __name__ == '__main__':
    run()
