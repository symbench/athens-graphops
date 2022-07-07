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
from tkinter import S
from .designer import Designer
from .architect import create_minimal
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
        # ignore parallel wings for now
        self.design_string = "".join([x for x in design_string if x != '\''])

        # keep track of possible attachment points and most recently added instances
        # instance --> (model, name, parameters)
        self.locator = None

    def summary(self):
        print(f"|-- design: {self.design_string}")
        print(f"|- # cxn groups: {self.get_connection_group_count()}")
        print(f"|- # branching connector: {self.get_branching_connector_count()}")
        print(f"|- # wings: {self.get_total_wing_count()}")
        print(f"|- # propellers: {self.get_total_prop_count()} ({self.get_vprop_count()} v, {self.get_hprop_count()} h)") 

    def get_connection_group_count(self):
        return self.design_string.count('[')

    def get_branching_connector_count(self):
        return self.design_string.count('(')
    
    def get_hprop_count(self):
        return self.design_string.count('h')

    def get_vprop_count(self):
        return self.design_string.count('p')

    def get_total_prop_count(self):
        return self.get_hprop_count() + self.get_vprop_count()

    def get_wing_count(self):
        return self.design_string.count('w')
    
    def get_parallel_wing_count(self):
        return self.design_string.count('w\'')

    def get_total_wing_count(self):
        return self.get_wing_count() + self.get_parallel_wing_count()

    def parse(self):
        """ get design instructions for the designer to map string to designer functions
        
            instructions format:

                {step (int): { designer_function: [ params ] } }
        """

        cylinder_diameter = 100
        port_thickness = 0.75 * cylinder_diameter
        # bar1_length = 700
        # bar2_length = 750
        bar_length = 500

        motor_model = "MAGiDRIVE150"
        propeller_model = "62x5_2_3200_46_1150"

        has_stear_wing = True
        stear_wing_naca = "0006"
        stear_wing_chord = 500
        stear_wing_span = 3000
        stear_wing_load = 1000

        # add motor_propeller - prop type 1 <--> h 
        # add cylinder --> add flip in/ flip out
        # add wing --> add battery

        # connections defined by instances and connectors 
        # todo manage instance and connection locations            

        instructions = {}
        
        """
        cylinder configs: -+-o (tail), -xo (side), -ox (top), ]-o (fork)
        """
        cyl_count = 5

        for i in range(cyl_count):
            angle = 0  # angle of one end e.g. | or /
            instructions[i] = {
                "add_cylinder": [
                    bar_length,
                    cylinder_diameter,
                    port_thickness,
                    angle,
                    "test_cylinder",
                    "mount_inst",
                    "mount_conn"
                ]
            }

        

        for i, c in enumerate(self.design_string):
            # offset from adding cylinders
            cur_idx = len(instructions) - 1 + i 
            if c == "(":
                print("start connection group")
            elif c == ")":
                print("end connection group")
            elif c == "w":
                print("add wing")
                instructions[cur_idx] = {
                    "add_wing": [
                        "test_wing",
                        stear_wing_naca,
                        stear_wing_chord,
                        stear_wing_span,
                        stear_wing_load,
                        "left/right_inst",
                        "left/right_conn"
                    ]
                }
            elif c == "p" or c == "h":
                ori = -1 if c == "h" else 1  # vertical/horizontal
                spi = -1 if c == "h" else 1  # cwise/ccwise
                print("add propeller")
                instructions[cur_idx] = {
                    "add_motor_propeller": [
                        motor_model,
                        propeller_model,
                        ori,  # horizontal
                        spi,  # cwise?
                        "test_motor_prop",
                        "mount_inst",
                        "mount_connector",
                        "controller_inst"
                    ]
                }

            self.instructions = instructions


    def build_design(self):
        self.designer = Designer()

        #print(getattr(self.designer, "add_wing"))

        if True:

            self.designer.create_design("test") 
            fuselage = self.designer.add_fuselage(name="fuselage",
                            length=2000,
                            sphere_diameter=1520,
                            middle_length=300,
                            tail_diameter=200,
                            floor_height=150,
                            seat_1_fb=1000,
                            seat_1_lr=-210,
                            seat_2_fb=1000,
                            seat_2_lr=210)
            self.designer.add_passenger(name="passenger1",
                            fuselage_inst=fuselage,
                            fuselage_conn="SEAT_1_CONNECTOR")
            self.designer.add_passenger(name="passenger2",
                            fuselage_inst=fuselage,
                            fuselage_conn="SEAT_2_CONNECTOR")
            
            wing_naca = "0015"
            wing_chord = 1400
            wing_span = 8000
            wing_load = 5000

            battery_model = "VitalyBeta"
            battery_voltage = 840
            battery_percent = 100

            right_wing = self.designer.add_wing(name="right_wing",
                                    naca=wing_naca,
                                    chord=wing_chord,
                                    span=wing_span,
                                    load=wing_load,
                                    left_inst=fuselage,
                                    left_conn="RIGHT_CONNECTOR")

            left_wing = self.designer.add_wing(name="left_wing",
                                    naca=wing_naca,
                                    chord=wing_chord,
                                    span=wing_span,
                                    load=wing_load,
                                    right_inst=fuselage,
                                    right_conn="LEFT_CONNECTOR")

            battery_controller = self.designer.add_battery_controller("battery_controller")

            self.designer.add_battery(battery_model,
                            name="right_battery",
                            naca=wing_naca,
                            chord=wing_chord,
                            span=wing_span,
                            mount_side=1,
                            voltage_request=battery_voltage,
                            volume_percent=battery_percent,
                            wing_inst=right_wing,
                            controller_inst=battery_controller)

            self.designer.add_battery(battery_model,
                            name="left_battery",
                            naca=wing_naca,
                            chord=wing_chord,
                            span=wing_span,
                            mount_side=2,
                            voltage_request=battery_voltage,
                            volume_percent=battery_percent,
                            wing_inst=left_wing,
                            controller_inst=battery_controller)

            # get instance information
            print(self.designer.instances)
    
            self.build_extras()

            self.designer.close_design()

    def build_extras(self):
        assert self.instructions, "no instructions"
        print(self.instructions)


def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--dstring", type=str, help="string representing the design to be built")
    parser.add_argument("--random", action='store_true', help="select a random design string")

    args = parser.parse_args(args)

    if args.random:
        sb = StringerBuilder(get_random_design())
        sb.summary()
        sb.parse()
        sb.build_design()


if __name__ == '__main__':
    run()