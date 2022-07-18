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
from tkinter import ALL, S
from tkinter.messagebox import NO

from pyparsing import Opt
from .designer import Designer, Instance
from .architect import create_minimal
from . import CONFIG
from typing import Optional, Tuple, Union
import json


datapath = "C:\\stringer\\data\\10"

def get_design_strings():
    with open(os.path.join(datapath, 'designs'), 'r') as f:
        designs = f.readlines()
    return list(filter(None, [d.rstrip() for d in designs]))

def get_random_design():
    designs = get_design_strings()
    return random.choice(designs)

SCHEMA_DATA =  json.loads(open(os.path.join("data", "corpus_schema.json")).read())
ALL_CONNECTORS = {c: v['connectors'] for c, v in SCHEMA_DATA.items()}
print(ALL_CONNECTORS)

ALLOWABLE_CONNECTIONS = {}


class Cursor:
    def __init__(self, design):

        self.design = design
        self.cur_inst = None
        self.cur_conn = None

    def update_location(self, next_inst: Instance , next_conn: str):
        print(f"changing Cursor instance from: {self.cur_inst} to {next_inst}")
        print(f"changing Cursor connection from: {self.cur_conn} to {next_conn}")
        self.cur_inst = next_inst
        self.cur_conn = next_conn

    def get_current_location(self):
        print(f"cursor current location: inst {self.cur_inst} conn {self.cur_conn}")

    def get_component_type_at_current_connection(self):
        for component, connectors in ALL_CONNECTORS.items():
            for connector, connect_dir in connectors.items():
                if self.cur_conn == connector:
                    return component

    def get_allowable_next_connection(self):
        """
        allowable connections:

        """
        pass

class StringerBuilder:
    def __init__(self, design_string):
        # ignore parallel wings for now
        self.design_string = "".join([x for x in design_string if x != '\''])

        self.design_name = "test"

        # keep track of positions during construction
        self.cursor = Cursor(self.design_name)

        # workflow direct2cad
        self.workflow = "uam_direct2cad"



    def summary(self):
        print(f"|-- design: {self.design_string}")
        print(f"|- # cxn groups: {self.get_connection_group_count()}")
        print(f"|- # branching connector: {self.get_branching_connector_count()}")
        print(f"|- # wings: {self.get_wing_count()}")
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
    
    def set_config_params(self):
        pass

    def build_extras(self):
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

        instructions = {} # todo make not dict
        
        """
        cylinder configs: -+-o (tail), -xo (side), -ox (top), ]-o (fork)
        """
        cyl_count = 5

        # ensure cursor is positioned
        assert self.cursor.cur_inst and self.cursor.cur_conn == "TOP_CONNECTOR"

        for i in range(cyl_count):
            angle = 0  # angle of one end e.g. | or /

            # instructions[i] = {
            #     "add_cylinder": [
            #         bar_length * 3, # length
            #         cylinder_diameter, # diameter
            #         port_thickness, # thickness
            #         f"cylinder_{i}", # name
            #         self.cursor.cur_inst, # instance to connect to
            #         self.cursor.cur_conn # connector to connect to
            #     ]
            # }

            cyl = self.designer.add_cylinder(
                bar_length * 3,
                cylinder_diameter,
                port_thickness,
                angle,
                f"cylinder_{i}",
                self.cursor.cur_inst,
                self.cursor.cur_conn
            )

            # go to the next location of the component just added
            self.cursor.update_location(cyl, "REAR_CONNECTOR")

        

        # for i, c in enumerate(self.design_string):
        #     # offset from adding cylinders
        #     cur_idx = len(instructions) - 1 + i 
        #     if c == "(":
        #         print("start connection group")
        #         # get components in () then connect them to the same cylinder
        #     elif c == ")":
        #         print("end connection group")
        #     elif c == "w":

                

        #         print("add wing")
        #         instructions[cur_idx] = {
        #             "add_wing": [
        #                 "test_wing",
        #                 stear_wing_naca,
        #                 stear_wing_chord,
        #                 stear_wing_span,
        #                 stear_wing_load,
        #                 "left/right_inst",
        #                 "left/right_conn"
        #             ]
        #         }
        #     elif c == "p" or c == "h":
        #         ori = -1 if c == "h" else 1  # vertical/horizontal
        #         spi = -1 if c == "h" else 1  # cwise/ccwise
        #         print("add propeller")
        #         instructions[cur_idx] = {
        #             "add_motor_propeller": [
        #                 motor_model,
        #                 propeller_model,
        #                 ori,  # horizontal
        #                 spi,  # cwise?
        #                 "test_motor_prop",
        #                 "mount_inst",
        #                 "mount_connector",
        #                 "controller_inst"
        #             ]
        #         }

        #     self.instructions = instructions


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

            # done building the minimal vehicle, set cursor for adding custom components
            self.cursor.fuselage = fuselage # store fuselage
            self.cursor.update_location(fuselage, "TOP_CONNECTOR")

            # add the non-minimal components to the rest of vehicle using the Cursor 
            self.build_extras()

            self.designer.close_design()

    # def build_extras(self):
    #     assert self.instructions, "no instructions"
    #     for seq_num, instruction in self.instructions.items():
    #         print(seq_num, instruction)


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
        #sb.parse()
        sb.build_design()


if __name__ == '__main__':
    run()