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

from typing import Any

import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def load_json(filename: str) -> Any:
    with open(os.path.join(DATA_DIR, filename), 'r') as file:
        return json.load(file)


CORPUS_DATA = load_json('corpus_data.json')

CORPUS_SCHEMA = load_json('corpus_schema.json')
