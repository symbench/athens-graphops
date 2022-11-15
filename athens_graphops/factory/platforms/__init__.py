#!/usr/bin/env python3
# Copyright (C) 2022, Peter Volgyesi
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
import importlib
import pkgutil
import inspect


def __discover_designs():
    """Automatically discover and import all design creation functions."""
    designs = {}
    for mod_info in pkgutil.walk_packages(__path__, __name__ + "."):
        mod = importlib.import_module(mod_info.name)
        for name, func in inspect.getmembers(mod, inspect.isfunction):
            prefix = "create_"
            if name.startswith(prefix):
                designs[name[len(prefix) :]] = func

    return designs


designs = __discover_designs()
