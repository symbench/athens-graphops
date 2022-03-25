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


def validate_corpus_data():
    with open(os.path.join(CONFIG["data_dir"], "corpus_data.json"), 'r') as file:
        corpus_data = json.load(file)
    with open(os.path.join(CONFIG["data_dir"], "corpus_schema.json"), 'r') as file:
        corpus_schema = json.load(file)

    counts = {cls: 0 for cls in corpus_schema.keys()}
    for mod in corpus_data:
        if mod["class"] not in corpus_schema:
            print("WARNING: unknown component class {}".format(mod["class"]))
            continue

        counts[mod["class"]] += 1
        cls = corpus_schema[mod["class"]]

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


def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--corpus-data', action='store_true',
                        help="validates the corpus against the schema")
    args = parser.parse_args(args)

    if args.corpus_data:
        validate_corpus_data()


if __name__ == '__main__':
    run()
