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

import os

from .dataset import CORPUS_DATA, CORPUS_SCHEMA, BATTERY_TABLE, MOTOR_TABLE, PROPELLER_TABLE

# these can be overwritten in __main__
CONFIG = {
    "hostname": "localhost",
    "timeout": 30,
    "script_dirs": [
        '.',
        os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts')),
        os.path.abspath(os.path.join(os.path.dirname(
            __file__), '..', 'autograph', 'scripts')),
    ],
    "batch_dirs": [
        '.',
        os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts')),
        os.path.abspath(os.path.join(os.path.dirname(
            __file__), '..', 'autograph')),
    ]
}
