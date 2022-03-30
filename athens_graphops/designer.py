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

from .query import Client


def create_minimal():
    client = Client()
    design = "Minimal"
    print("Creating design", design)

    client.create_design(design)
    client.create_instance(design, "FUSE_SPHERE_CYL_CONE", "fuselage")
    client.create_instance(design, "Orient", "Orient")
    client.create_connection(
        design, "Orient", "ORIENTCONN", "fuselage", "ORIENT")
    client.orient_design(design, "Orient")

    client.close()


def create_many_cylinders():
    client = Client()
    design = "ManyCylinders"
    print("Creating design", design)

    client.create_design(design)
    client.create_instance(design, "FUSE_SPHERE_CYL_CONE", "fuselage")
    client.create_instance(design, "Orient", "Orient")
    client.create_connection(
        design, "Orient", "ORIENTCONN", "fuselage", "ORIENT")

    def create_parameter(instance: str, name: str, value: float):
        param_name = instance + "_" + name
        client.create_parameter(design, param_name, value)
        client.assign_parameter(design, instance, name, param_name)

    previous = "fuselage"
    next_cylid = 1

    def attach_cylinder(diameter: float, length: float,
                        port_thickness: float):
        # observed requirements in CREO, but min port_thickness is flaky
        assert 3 <= port_thickness < diameter <= length
        nonlocal previous, next_cylid

        instance = "CYL{:03}".format(next_cylid)
        print("Creating instance", instance)
        client.create_instance(design, "PORTED_CYL", instance)
        create_parameter(instance, "DIAMETER", diameter)
        create_parameter(instance, "LENGTH", length)
        create_parameter(instance, "PORT_THICKNESS", port_thickness)
        client.create_connection(
            design, previous, "REAR_CONNECTOR", instance, "FRONT_CONNECTOR")

        next_cylid += 1
        previous = instance

    for diameter in [10, 20, 30, 50, 100, 150, 200]:
        for port_thickness in [8, 15, 25, 40, 80, 150]:
            if not port_thickness < diameter:
                continue
            for length in [20, 30, 50, 100, 200, 300, 400, 500]:
                if not diameter <= length:
                    continue
                attach_cylinder(
                    diameter=diameter,
                    port_thickness=port_thickness,
                    length=length)

    client.orient_design(design, "Orient")
    client.close()


def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--many-cylinders', action='store_true',
                        help="creates lots of ported cylinders")
    parser.add_argument('--minimal', action='store_true',
                        help="creates a minimal a design")
    args = parser.parse_args(args)

    if args.many_cylinders:
        create_many_cylinders()
    elif args.minimal:
        create_minimal()


if __name__ == '__main__':
    run()
