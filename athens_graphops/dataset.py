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

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def load_json(filename: str) -> Any:
    try:
        with open(os.path.join(DATA_DIR, filename), 'r') as file:
            return json.load(file)
    except:
        return []


CORPUS_DATA = load_json('corpus_data.json')

CORPUS_SCHEMA = load_json('corpus_schema.json')


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
