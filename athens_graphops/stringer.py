#!/usr/bin/env python3
# Copyright (C) 2022, Michael Sandborn
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
import random
from .designer import Designer
from . import CONFIG

datapath = "C:\\stringer\\data\\10"

def get_design_strings():
    with open(os.path.join(datapath, 'designs'), 'r') as f:
        designs = f.readlines()
    return list(filter(None, [d.rstrip() for d in designs]))

def get_random_design():
    designs = get_design_strings()
    return random.choice(designs)


class StringerBuilder:
    def __init__(self, design_string):
        self.design_string = design_string
        self.designer = None

    def get_connection_group_count(self):
        return self.design_string.count('[')

    def summary(self):
        print(f"|-- design: {self.design_string}")
        print(f"|- # cxn groups: {self.get_connection_group_count()}")
        print(f"|- # wings: {self.get_wing_count()}")
        print(f"|- # propellers: {self.get_total_prop_count()} ({self.get_vprop_count()} v, {self.get_hprop_count()} h)") 

    def get_hprop_count(self):
        return self.design_string.count('h')

    def get_vprop_count(self):
        return self.design_string.count('p')

    def get_total_prop_count(self):
        return self.get_hprop_count() + self.get_vprop_count()

    def get_wing_count(self):
        return self.design_string.count('w')

    def parse(self):
        self.design_dict = {}


def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--dstring", type=str, help="string representing the design to be built")
    parser.add_argument("--random", action='store_true', help="select a random design string")

    args = parser.parse_args(args)
    print(args)

    if args.random:
        sb = StringerBuilder(get_random_design())
        sb.summary()


if __name__ == '__main__':
    run()