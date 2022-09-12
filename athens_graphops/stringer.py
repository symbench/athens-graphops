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
from turtle import right

from pyparsing import Opt
from sympy import nextprime
from .designer import Designer, Instance
from .architect import Architect
from . import CONFIG
from typing import Optional, Tuple, Union
import json
from collections import OrderedDict


datapath = "C:\\stringer\\data\\10"

def get_design_strings(filepath):
    with open(filepath, 'r') as f:
        designs = f.readlines()
    return list(filter(None, [d.rstrip() for d in designs]))

SCHEMA_DATA =  json.loads(open(os.path.join("data", "corpus_schema.json")).read())
ALL_CONNECTORS = {c: v['connectors'] for c, v in SCHEMA_DATA.items()}

CYLINDER_CONNECTORS = ["BOTTOM_CONNECTOR",
                       "LEFT_CONNECTOR",
                       "REAR_CONNECTOR",
                       "RIGHT_CONNECTOR",
                       "TOP_CONNECTOR", 
                       "FRONT_CONNECTOR"]

class Cursor:
    """ track connection locations through connectors and instances
        during vehicle construction, each design has a single cursor associated with it
    """
    def __init__(self, design):

        self.design = design
        #dummy = Instance("dummy_model", "dummy_name")
        self.cur_inst = None
        self.cur_conn = "init"
        
        #  keep track of whether the connectors of each instance are occupied
        # {instance: [connnectors : is_occupied ]}
        self.connections = {}

        self.directions = list("uldr")
        self.connector_names = ["TOP", "LEFT", "BOTTOM", "RIGHT"]
        self.direction_connector_map = { p[0]: p[1] + "_CONNECTOR" for p in list(zip(self.directions, self.connector_names))}

        print(f"self.direction_connector_map: {self.direction_connector_map}")

        # used to determine when to halt design construction
        self.substructures = {
            'wing_pair': 0,
            'rail': 0,
            'crossbar': 0,
            'motor_prop': 0,
            'tbar': 0,
            'wing_single': 0,
            'fuselage': 0,
        }

    def update_location(self, next_inst: Instance , next_conn: str):
        print(f"changing Cursor instance from: {self.cur_inst.name} to {next_inst.name}")
        print(f"changing Cursor connection from: {self.cur_conn} to {next_conn}")
        self.cur_inst = next_inst
        self.cur_conn = next_conn

    def get_current_location(self):
        print(f"cursor current location: inst {self.cur_inst} conn {self.cur_conn}")

    def get_component_type_at_current_connection(self):
        for component, connectors in ALL_CONNECTORS.items():
            for connector, _ in connectors.items():
                if self.cur_conn == connector:
                    return component


class StringerBuilder:
    def __init__(self, design_file, batch_size = 10):

        self.design_name = "test"
        self.design_file = design_file
        self.designs_to_build = get_design_strings(self.design_file)
        print(f"designs to build: {len(self.designs_to_build)}")

        self.workflow = "uam_direct2cad"

        # possible ways that a vehicle substructure can protrude.
        # letters correspond to up, left, down, right.
        
        self.directions = list("uldrfb")

        # relative sizes of the substructure 
        # letters correspond to small (1 cyl/unit), medium (2), large (3)
        #self.sizes = list("sml")

    def get_random_cylinder_connector(self):
        return random.choice(["BOTTOM", "TOP", "LEFT", "RIGHT"]) + "_CONNECTOR"

    def resolve_connectors(self, substructure: str = 'tbar', direction: str = 'l'):
        """ Provide the appropriate connector(s) given the substructure name and the
            requested orientation direction
        """
        if direction == 'l':
            return "RIGHT_CONNECTOR"
        elif direction == 'r':
            return "LEFT_CONNECTOR"

    def resolve_angles(self, substructure: str = 'fork', direction: str = 'u'):
        """ Provide the appropriate connection angles given the substructure name and the
            requested orientation
        """
        assert substructure in ['fork', 'tbar']

        if substructure == 'fork':
            if direction == 'u':
                fork_left_angle = 90
                fork_right_angle = 90
                post_left_angle = 270
                post_right_angle = 90  
            elif direction == 'd':
                fork_left_angle = 270
                fork_right_angle = 270
                post_left_angle = 90
                post_right_angle = 270
            elif direction == 'l':
                fork_left_angle = 180
                fork_right_angle = 180
                post_left_angle = 270
                post_right_angle = 90
            elif direction == 'r':
                fork_left_angle = 270
                fork_right_angle = 180
                post_left_angle = 270
                post_right_angle = 270
            elif direction == 'b':
                fork_left_angle = 180
                fork_right_angle = 180
                post_left_angle = 360
                post_right_angle = 90
            return (fork_left_angle, fork_right_angle), (post_left_angle, post_right_angle)
        elif substructure == 'tbar':
            if direction == 'u':  # T
                return (90, 180)

    def make_motor_prop(self, motor_model: str = "MAGiDRIVE150", propeller_model: str="62x5_2_3200_46_1150",
                        prop_type:int = 1, direction: int = 1,
                            mount_inst: Optional[Instance] = None,
                            mount_conn: Optional[str] = None,
                            controller_inst: Optional[Instance] = None):
        name = f"motor_prop_{self.cursor.substructures['motor_prop']+1}"

        motor, prop = self.designer.add_motor_propeller(motor_model, propeller_model, prop_type, direction,
                                        name_prefix=name, mount_inst=mount_inst, mount_conn=mount_conn,
                                        controller_inst=controller_inst)
    
        self.cursor.substructures['motor_prop'] += 1

        return [motor, prop], [name]

    def make_wing_pair(self, bar_length: float=1200, cylinder_diameter: float=100,
                    port_thickness: float=75, wing_naca: str="0006", wing_span: int = 3000,
                    wing_load: int = 1000, wing_chord: int = 500, start_inst: Instance =None,
                    start_conn: str = "REAR_CONNECTOR", max_angle_between: int = 90):
        
        """ Create a pair of wings on a cylinder with the specified angle between them """
        
        # assume start at cylinder for now
        #self.cursor.update_location(start_inst, start_conn)

        name =  f"wing_pair_{self.cursor.substructures['wing_pair'] + 1}"

        # random cylinder rotation for wing separation
        angle_between = random.choice(list(range(0, max_angle_between, 15)))

        wing_cylinder = self.designer.add_cylinder(
                bar_length,
                cylinder_diameter,
                port_thickness,
                angle_between, #  front angle cylinder rotation about long axis wrt to mount inst
                name, 
                start_inst,
                start_conn
        )

        right_conn = self.get_random_cylinder_connector()
        self.cursor.update_location(wing_cylinder, right_conn)  # "RIGHT_CONNECTOR"

        right_wing = self.designer.add_wing(name=f"wing_pair_{self.cursor.substructures['wing_pair'] + 1}_r",
                                    naca=wing_naca,
                                    chord=wing_chord,
                                    span=wing_span,
                                    load=wing_load,
                                    left_inst=self.cursor.cur_inst,
                                    left_conn=self.cursor.cur_conn)
        
        left_conn = self.get_complement_cyl_connector(right_conn)
        self.cursor.update_location(wing_cylinder, left_conn)  # "TOP_CONNECTOR"
        left_wing = self.designer.add_wing(name=f"wing_pair_{self.cursor.substructures['wing_pair'] + 1}_l",
                                naca=wing_naca,
                                chord=wing_chord,
                                span=wing_span,
                                load=wing_load,
                                right_inst=self.cursor.cur_inst,
                                right_conn=self.cursor.cur_conn)

        self.cursor.substructures['wing_pair'] += 1

        return [wing_cylinder, left_wing, right_wing], [name], [left_conn, right_conn]  #, left_wing, right_wing

    def make_single_wing(self, bar_length: float=1200, cylinder_diameter: float=100,
                    port_thickness: float=75, wing_naca: str="0006", wing_span: int = 3000,
                    wing_load: int = 1000, wing_chord: int = 500, start_inst: Instance =None,
                    start_conn: str = "REAR_CONNECTOR", direction: str='u'):

        direction = random.choice(self.cursor.directions)
        #assert direction in self.cursor.directions, f"invalid direction: {direction}. Valid wing directions are {self.cursor.directions}"
                    # assume start at cylinder for now
        #self.cursor.update_location(start_inst, start_conn)

        name =  f"wing_single_cylinder_{self.cursor.substructures['wing_single'] + 1}"
        # create the cylinder that will have 2 NACA ports on it
        wing_cylinder = self.designer.add_cylinder(
                bar_length,
                cylinder_diameter,
                port_thickness,
                0, #  front angle- degrees of cylinder rotation on created cylinder wrt to its connected instance
                name, 
                start_inst,
                start_conn
        )

        connector = self.cursor.direction_connector_map[direction]

        self.cursor.update_location(wing_cylinder, connector)

        solo_wing = self.designer.add_wing(name=f"wing_single_{direction}_{self.cursor.substructures['wing_single'] + 1}",
                                    naca=wing_naca,
                                    chord=wing_chord,
                                    span=wing_span,
                                    load=wing_load,
                                    left_inst=self.cursor.cur_inst,
                                    left_conn=self.cursor.cur_conn)

        self.cursor.substructures['wing_single'] += 1
        
        return [wing_cylinder, solo_wing], [name], [connector]

    
    def build_spec(self, design_idx, spec_dict):
        """ build a design from a specification dictionary of connections
            and instances which are derived from the string representation"""
        print("in build_spec")
        
        design_name = list(spec_dict.keys())[design_idx]

        print(f"now building {design_name} with {len(spec_dict[design_name])} total structures")
        
         # init design and cursor 
        self.designer = Designer()
        self.designer.create_design("spec")

        # vehicle is ordered dict of {'substructure: {inst: })}
        self.vehicle_instances[design_name] = OrderedDict()
        self.vehicle_histories[design_name] = OrderedDict()

        fuselage, battery_controller = self.build_minimal()

        self.cursor = Cursor(design_name)
        self.cursor.fuselage = fuselage

        next_inst = fuselage
        next_conn = self.select_connector("fuselage")
        self.cursor.update_location(next_inst, next_conn)

        # convert strings in design map to corresponding functions to call

        # todo need to account for left and right connectors
        connector_map = {
            "front_connector": "FRONT_CONNECTOR",
            "bottom_connector": "BOTTOM_CONNECTOR",
            "back_connector": "REAR_CONNECTOR",
            "top_connector": "TOP_CONNECTOR"
        }

        structure_func_map = {
            "fourWay": self.make_crossbar,
            "fuselage": self.make_fuselage,
            "wing": self.make_wing_pair,
            "prop": self.make_motor_prop
        }

        def get_start_conn(prev_inst):
            """ given the connection list """
            return None
    
        prev_inst = None
        prev_conn = None
        for structure, connection_list in spec_dict[design_name].items():
            print(f"structure: {structure}")
            print(f"connections: {connection_list}")

            # get the component to create
            make_component_func = structure_func_map[structure]
            # get start conn from prev inst
            start_conn = get_start_conn(prev_inst)

            inst_list, name = make_component_func(prev_inst, start_conn)




        self.designer.close_design()



    def run_builder_loop(self, num_designs=1, build_from_spec=False, spec_filepath=None):
        """ the main loop to build a set of stringer designs
            through the uam_direct2cad workflow in jenkins
        """

        # keep track of the steps taken to build each vehicle
        self.vehicle_histories = OrderedDict()
        self.vehicle_instances = OrderedDict()

        print("in run builder loop")

        if build_from_spec and spec_filepath is not None:
            assert os.path.exists(spec_filepath), "vehicle specification file not found!"
            spec_dict = json.loads(open(spec_filepath, 'r').read())
            design_count = len(spec_dict)
        else:
            design_count = num_designs

        for x in range(design_count):     #len(self.designs_to_build)):
            print(f"building design {x+1}/{design_count}")
            
            if build_from_spec:
                cur_design_name = f"spec_{x}"
                self.build_spec(x, spec_dict)
                design = "spec"
            else:
                cur_design_name = f"random_{x}"
                self.build_random(cur_design_name)
                design = "random"
            
            self.run_design(design)

        print("writing vehicle histories")
        import time
        timestr = time.strftime("%Y%m%d-%H%M%S")
        with open("./design_history_json/design_history_" + timestr + ".json", 'w') as f:
            json.dump(self.vehicle_histories, f)

        print("done")
        self.architect.close_jenkins_client()
            



    def make_fork(self, bar_length: float, cylinder_diameter: float,
                    port_thickness: float, start_inst: Instance=None, 
                    start_conn: str = None, size:str ='s', direction: str ='u'):
        """ Create a fork in the vehicle that originates at 'start'
            and extends in 'direction', maybe do basic interference checking
            e.g. --[
        """
        # go to the next location of the component just added
        self.cursor.update_location(start_inst, start_conn) #"LEFT_CONNECTOR")

        # (left, right) -- angles for the bases and posts of the fork
        fork_angles, post_angles = self.resolve_angles('fork', direction)

        # create forked tail
        fork_l = self.designer.add_cylinder(
                bar_length*3,
                cylinder_diameter,
                port_thickness,
                fork_angles[0],
                f"fork_l_{self.cursor.substructures['fork'] + 1}",
                self.cursor.cur_inst,
                self.cursor.cur_conn
            )

        # go to the next location of the component just added
        self.cursor.update_location(start_inst, "RIGHT_CONNECTOR")

        # create forked tail
        fork_r = self.designer.add_cylinder(
                bar_length*3,
                cylinder_diameter,
                port_thickness,
                fork_angles[1],
                f"fork_r_{self.cursor.substructures['fork'] + 1}",
                self.cursor.cur_inst,
                self.cursor.cur_conn
            )

        self.cursor.update_location(fork_l, "TOP_CONNECTOR")

         # create post
        post_l = self.designer.add_cylinder(
                bar_length,
                cylinder_diameter,
                port_thickness,
                post_angles[0],
                f"post_l_{self.cursor.substructures['fork'] + 1}",
                self.cursor.cur_inst,
                self.cursor.cur_conn
            )
        
        self.cursor.update_location(fork_r, "BOTTOM_CONNECTOR")

        # create post
        post_r = self.designer.add_cylinder(
                bar_length,
                cylinder_diameter,
                port_thickness,
                post_angles[1],
                f"post_r_{self.cursor.substructures['fork'] + 1}",
                self.cursor.cur_inst,
                self.cursor.cur_conn
            )
        
        self.cursor.substructures['fork'] += 1
        return post_l, post_r



    def make_tbar(self, bar_length: float=500, cylinder_diameter: float=100, port_thickness: float=75,
                    start_inst: Instance=None, start_conn: str = None, size:str ='s',
                    direction: str ='r'):
        """ Create a T-bar for the vehicle of size and direction """

        post_name= f"tbar_post_{self.cursor.substructures['tbar'] + 1}"
        cross_name= f"tbar_cross_{self.cursor.substructures['tbar'] + 1}"

        t_post = self.designer.add_cylinder(
                bar_length,
                cylinder_diameter,
                port_thickness,
                front_angle=0,
                name=post_name,
                mount_inst=start_inst,
                mount_conn=start_conn
            )

        cross_connector = self.get_random_cylinder_connector()

        self.cursor.update_location(t_post, cross_connector)

        t_cross = self.designer.add_cylinder(
                bar_length,
                cylinder_diameter,
                port_thickness,
                front_angle=0,
                name=cross_name,
                mount_inst=self.cursor.cur_inst,
                mount_conn=self.cursor.cur_conn
            )

        self.cursor.update_location(start_inst, "REAR_CONNECTOR")

        self.cursor.substructures['tbar'] += 1
        return [t_post, t_cross], [post_name, cross_name], [cross_connector]

    def make_crossbar(self, bar_length: float=500, cylinder_diameter: float=100, port_thickness: float=75,
                    start_inst: Instance=None, start_conn: str=None):
        """ Create a crossbar of the 
            e.g. +
        """

        hub_name = f"cross_bar_{self.cursor.substructures['crossbar']+1}"

        side_cyls = []
        side_names = []
        def fill_connectors(start_inst, center_name):
            for cyl_connector in ["TOP", "BOTTOM", "LEFT", "RIGHT"]:
                cname = center_name+"_"+cyl_connector
                c = self.designer.add_cylinder(
                    bar_length,
                    cylinder_diameter,
                    port_thickness,
                    name=cname,
                    mount_inst=start_inst,
                    mount_conn=cyl_connector+"_CONNECTOR")
                side_cyls.append(c)
                side_names.append(cname)

        #self.cursor.update_location(start_inst, start_conn)
        hub_cyl = self.designer.add_cylinder(bar_length / 5,
                                    cylinder_diameter,
                                    port_thickness,
                                    name=hub_name,
                                    mount_inst=start_inst,
                                    mount_conn=start_conn)
                    
        fill_connectors(hub_cyl, hub_name)

        self.cursor.substructures['crossbar'] += 1

        return [hub_cyl] + side_cyls, [hub_name] + side_names


    def make_rail(self, bar_length: float = 1000, cylinder_diameter: float = 100, port_thickness: float = 75,
                    start_inst: Instance=None, start_conn: str=None, is_base_rail=False, name=None, alt_orig_cyl_connector: str = None):
        """ Create a length of parallel rails to add to the vehicle in the same
            way described in fork
            e.g. ===
        """

        if not is_base_rail:
            name = f"rail_{self.cursor.substructures['rail']+1}"
        assert name is not None  # if the added rail is a base rail, `name` should be supplied
        
        # alt_orig_connector allows for specifying cylinders to be connected to the `mount_connector` with something
        # other than the default `FRONT_CONNECTOR` connector
        if alt_orig_cyl_connector is not None:

            rail_cyl = self.designer.add_cylinder(
                        bar_length,
                        cylinder_diameter,
                        port_thickness,
                        front_angle=0,
                        name=name,
                        mount_inst=start_inst,
                        mount_conn=start_conn,
                        alt_connector=alt_orig_cyl_connector)
        else:
            rail_cyl = self.designer.add_cylinder(
                        bar_length,
                        cylinder_diameter,
                        port_thickness,
                        front_angle=0,
                        name=name,
                        mount_inst=start_inst,
                        mount_conn=start_conn)

        # hack for making non-base rails
        if not is_base_rail:
            self.cursor.substructures['rail'] += 1

        return [rail_cyl], [name], []  # empty list of intermediate connectors

    
    def select_connector(self, component):

        connectors = {
            "fuselage": [
                "BOTTOM_CONNECTOR",
                "REAR_CONNECTOR",
                "TOP_CONNECTOR"],
            "cylinder": [
                "BOTTOM_CONNECTOR",
                "FRONT_CONNECTOR",
                "LEFT_CONNECTOR",
                "REAR_CONNECTOR",
                "RIGHT_CONNECTOR",
                "TOP_CONNECTOR"]
        }
        return random.choice(connectors[component])
        

    def get_complement_cyl_connector(self, connector: str):
        if connector == "TOP_CONNECTOR":
            return "BOTTOM_CONNECTOR"
        elif connector == "BOTTOM_CONNECTOR":
            return "TOP_CONNECTOR"
        elif connector == "LEFT_CONNECTOR":
            return "RIGHT_CONNECTOR"
        elif connector == "RIGHT_CONNECTOR":
            return "LEFT_CONNECTOR"
        elif connector == "FRONT_CONNECTOR":
            return "REAR_CONNECTOR"


    def build_random(self, design_name, max_component_count=16):
        
        num_components = random.randint(5, max_component_count)
        components = ["rail", "wing_pair", "wing_single", "crossbar", "motor_prop", "tbar"]
        component_weights = [0.1, 0.2, 0.15, 0.15, 0.3, 0.15]

        print(f"now building {design_name} with {num_components} total components")
        
         # init design and cursor 
        self.designer = Designer()
        self.designer.create_design("random")

        # vehicle is ordered dict of {'substructure: {inst: })}
        self.vehicle_instances[design_name] = OrderedDict()
        self.vehicle_histories[design_name] = OrderedDict()

        self.cursor = Cursor(design_name)
        fuselage, battery_controller = self.build_minimal()
        self.cursor.cur_inst = fuselage
        self.cursor.fuselage = fuselage

        def get_vehicle_components():
            return random.choices(components, component_weights, k=num_components)

        vehicle_components = get_vehicle_components()
        print(f"vehicle components: {vehicle_components}")

        # location to add first component after building minimal
        next_inst = fuselage
        next_conn = self.select_connector("fuselage")
        self.cursor.update_location(next_inst, next_conn)

        # inst name to a set of occupied connectors; compute candidate propeller locations from 
        # this information using set difference
        inst_to_available_connectors = {}

        def update_available_connectors(occupied):
            occupied = [] if occupied is None else occupied
            return set(CYLINDER_CONNECTORS) - set(occupied)

        for component in vehicle_components:

            orig_inst = self.cursor.cur_inst
            orig_conn = self.cursor.cur_conn

            # add component to next_conn

            # for each make_x function, we return an instance list and a name list
            # regardless of the instance list length, we adopt the convention that
            # the first element of this list will be the `next_inst`and should always (for now)
            # be a cylinder instance

            inst_to_available_connectors[orig_inst.name] = update_available_connectors(orig_conn)

            if component == "rail":
                rail_inst_list, rail_name_list, _ = self.make_rail(start_inst=orig_inst,
                                                   start_conn=orig_conn)
                added_inst = rail_inst_list[0]
                struct_name = rail_name_list[0]

                # update the newly added instance with the set of occupied connectors, may be empty
                inst_to_available_connectors[added_inst.name] = update_available_connectors("FRONT_CONNECTOR")

            elif component == "tbar":
                tbar_inst_list, tbar_name_list, connector_list = self.make_tbar(
                    start_inst=orig_inst, start_conn=orig_conn)
                # select a random anchor instance for future connections
                added_inst = random.choice(tbar_inst_list)
                struct_name = tbar_name_list[0]  # use tpost name to reference structure

                # indicate that the tbar post at the returned cross connector list is occupied
                inst_to_available_connectors[tbar_inst_list[0].name] = update_available_connectors(connector_list[0])
                inst_to_available_connectors[tbar_inst_list[1].name] = update_available_connectors("FRONT_CONNECTOR")

            elif component == "crossbar":
                #  no need to return connections, hubs will always be filled
                crossbar_inst_list, crossbar_name_list = self.make_crossbar(start_inst=orig_inst, start_conn=orig_conn)
                added_inst = random.choice(crossbar_inst_list[1:])  # select a non-hub cylinder
                struct_name = crossbar_name_list[0]  # use hub name to reference structure

                # indicate occupied hub and attached front connectors
                inst_to_available_connectors[crossbar_inst_list[0].name] = update_available_connectors([c + "_CONNECTOR" for c in ["TOP", "BOTTOM", "LEFT", "RIGHT"]])
                for cyl_inst in crossbar_inst_list[1:]:
                    inst_to_available_connectors[cyl_inst.name] = update_available_connectors("FRONT_CONNECTOR")

            elif component == "wing_pair":
                wingpair_inst_list, wingpair_name_list, connector_list = self.make_wing_pair(start_inst=orig_inst, start_conn=orig_conn)
                added_inst = wingpair_inst_list[0]
                struct_name = wingpair_name_list[0]

                inst_to_available_connectors[wingpair_inst_list[0].name] = update_available_connectors(connector_list)

            elif component == "wing_single":
                wingsingle_inst_list, wingsingle_name_list, connector_list = self.make_single_wing(start_inst=orig_inst, start_conn=orig_conn)
                added_inst = wingsingle_inst_list[0]
                struct_name = wingsingle_name_list[0]

                inst_to_available_connectors[wingsingle_inst_list[0].name] = update_available_connectors(connector_list)
            
            elif component == "motor_prop":
                print(f"skipping motor/prop")
                # hack the count to keep track of motor and prop without adding them for now
                self.cursor.substructures['motor_prop'] += 1

                # self.vehicle_histories[design_name]['candidate_prop_locs'][component + "_" + str(self.cursor.substructures['motor_prop'])] = {
                #     "orig_inst_name": orig_inst.name,
                #     "orig_inst_model": orig_inst.model,
                #     "orig_conn": orig_conn
                # }


                # motor, struct_name = self.make_motor_prop(mount_inst=self.cursor.cur_inst,
                #                                    mount_conn=self.cursor.cur_conn,
                #                                    controller_inst=battery_controller)
                # added_inst = motor
                continue

            # update vehicle build history
            # {struct_name : (added instance, origin connection)}
            self.vehicle_histories[design_name][struct_name] = {"orig_inst_name": orig_inst.name,
                                                                "orig_inst_model": orig_inst.model,
                                                                "orig_conn": orig_conn,
                                                                "next_inst_name": added_inst.name,
                                                                "next_inst_model": added_inst.model,
                                                                "next_conn": next_conn}
                                                                
            self.vehicle_instances[design_name][struct_name] =  added_inst

            if component != "motor_prop":
                # we added a non terminal, can connect directly from here
                next_inst = added_inst
            else:
                # we added a motor and prop (terminal), go to a random connector of a random instance
                random_substructure = random.choice(list(self.vehicle_histories[design_name].keys()))
                while "motor_prop" in random_substructure:
                    random_substructure = random.choice(list(self.vehicle_histories[design_name].keys()))
                next_inst = self.vehicle_instances[design_name][random_substructure]  # anchor instance, first element of tuple

            # try to keep symmetry
            next_conn = self.get_complement_cyl_connector(orig_conn)
            #self.select_connector("cylinder")

            # update available connectors

            # update next connector and cursor position
            self.cursor.update_location(next_inst, next_conn)

        # final substructure counts
        print(self.cursor.substructures)

        # get unoccupied
        self.vehicle_histories[design_name]['candidate_prop_locs'] = {inst_name: list(conn_set) for inst_name, conn_set in inst_to_available_connectors.items()}

        # end design
        self.designer.close_design()
        

    def build_dummy(self):
        """ function to hack on structure implementations """
        print(f"build_dummy")

        # init design and cursor 
        self.designer = Designer()
        self.designer.create_design("dummy")
        fuselage = self.build_minimal()

        self.cursor = Cursor("dummy")
        self.cursor.fuselage = fuselage
        self.cursor.update_location(fuselage, "REAR_CONNECTOR")


        """ Use this function to hack on substructures """
        cylinder_diameter = 100
        port_thickness = 0.75 * cylinder_diameter
        # bar1_length = 700
        # bar2_length = 750
        bar_length = 500

        motor_model = "MAGiDRIVE150"
        propeller_model = "62x5_2_3200_46_1150"
        lil_prop = "27x11_5_1800_51_70"
        big_prop = "90x86_2_200_46_100"

        has_stear_wing = True
        stear_wing_naca = "0006"
        stear_wing_chord = 500
        stear_wing_span = 3000
        stear_wing_load = 1000      
        
        tail_cyl_count = 4

        fork_posts = []
        tail_cylinder = None
        for i in range(tail_cyl_count):
            angle = 0  # angle of one end e.g. | or /

            cyl = self.designer.add_cylinder(
                bar_length * 4,
                cylinder_diameter,
                port_thickness,
                angle,
                f"cylinder_{i}",
                self.cursor.cur_inst,
                self.cursor.cur_conn
            )

            post_l, post_r = self.make_fork(bar_length, cylinder_diameter, port_thickness, 
                    cyl, "LEFT_CONNECTOR")
            
            fork_posts.extend([post_l, post_r])

            if i == tail_cyl_count - 1:
                tail_cylinder = cyl

            # go to the next location of the component just added
            self.cursor.update_location(cyl, "REAR_CONNECTOR")
        
        pl, pr = self.make_fork(bar_length, cylinder_diameter, port_thickness, 
                    self.cursor.cur_inst, "LEFT_CONNECTOR")
        fork_posts.extend([pl, pr])

        # tp1, tc1 = self.make_tbar(bar_length*2, cylinder_diameter, port_thickness,
        #             self.cursor.fuselage, "TOP_CONNECTOR")

        tp2, tc2 = self.make_tbar(bar_length*2, cylinder_diameter, port_thickness,
                    self.cursor.fuselage, "BOTTOM_CONNECTOR")

        # self.cursor.update_location(tc1, "REAR_CONNECTOR")
        # self.designer.add_motor_propeller(motor_model=motor_model,
        #                              prop_model=propeller_model,
        #                              prop_type=1,
        #                              direction=1,
        #                              name_prefix=f"t_cross_mp_top",
        #                              mount_inst=self.cursor.cur_inst,
        #                              mount_conn=self.cursor.cur_conn,
        #                              controller_inst=self.battery_controller)

        self.cursor.update_location(tc2, "REAR_CONNECTOR")
        self.designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     prop_type=1,
                                     direction=1,
                                     name_prefix=f"t_cross_mp_bottom",
                                     mount_inst=self.cursor.cur_inst,
                                     mount_conn=self.cursor.cur_conn,
                                     controller_inst=self.battery_controller)
        

        # self.cursor.update_location(tp1, "REAR_CONNECTOR")
        # self.designer.add_motor_propeller(motor_model=motor_model,
        #                              prop_model=propeller_model,
        #                              prop_type=1,
        #                              direction=1,
        #                              name_prefix=f"t_post_mp_top",
        #                              mount_inst=self.cursor.cur_inst,
        #                              mount_conn=self.cursor.cur_conn,
        #                              controller_inst=self.battery_controller)
            
        self.cursor.update_location(tp2, "REAR_CONNECTOR")
        self.designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     prop_type=1,
                                     direction=-1,
                                     name_prefix=f"t_post_mp_bottom",
                                     mount_inst=self.cursor.cur_inst,
                                     mount_conn=self.cursor.cur_conn,
                                     controller_inst=self.battery_controller)

        for i in range(len(fork_posts)):
            self.cursor.update_location(fork_posts[i], "REAR_CONNECTOR")
            self.designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     prop_type=1,
                                     direction=1,
                                     name_prefix=f"fork_post_mp_{i+1}",
                                     mount_inst=self.cursor.cur_inst,
                                     mount_conn=self.cursor.cur_conn,
                                     controller_inst=self.battery_controller)
                
        tp1, tc1 = self.make_tbar(bar_length*2, cylinder_diameter, port_thickness,
                    self.cursor.cur_inst, self.cursor.cur_conn)
        
        self.cursor.update_location(tp1, "REAR_CONNECTOR")
        self.designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     prop_type=1,
                                     direction=1,
                                     name_prefix=f"tail_tbar_post_mp",
                                     mount_inst=self.cursor.cur_inst,
                                     mount_conn=self.cursor.cur_conn,
                                     controller_inst=self.battery_controller)

        wing_cyl, l_wing, r_wing = self.make_wing_pair(bar_length,
                                                        cylinder_diameter,
                                                        port_thickness,
                                                        stear_wing_naca,
                                                        stear_wing_span,
                                                        stear_wing_load,
                                                        stear_wing_chord,
                                                        tail_cylinder)
        
        self.cursor.update_location(wing_cyl, "REAR_CONNECTOR")

        self.designer.add_motor_propeller(motor_model=motor_model,
                                     prop_model=propeller_model,
                                     prop_type=-1,
                                     direction=1,
                                     name_prefix=f"tail_tbar_cross_mp",
                                     mount_inst=self.cursor.cur_inst,
                                     mount_conn=self.cursor.cur_conn,
                                     controller_inst=self.battery_controller)

        # add cross_bars
        self.make_crossbar(cylinder_diameter, port_thickness, self.cursor.fuselage, "TOP_CONNECTOR")

        self.designer.close_design()

    def make_fuselage(self,
                      orig_inst: Optional[Instance] = None,
                      orig_conn: Optional[str] = None,
                      dest_conn: Optional[str] = "REAR_CONNECTOR"):
        fuse_length = 2000
        fuse_sphere_diameter = 1520
        fuse_middle_length = 750
        fuse_tail_diameter = 200
        fuse_floor_height = 150
        fuse_seat_1_fb = 1000
        fuse_seat_1_lr = -210
        fuse_seat_2_fb = 1000
        fuse_seat_2_lr = 210
        fuse_top_port_disp = 300
        fuse_bottom_port_disp = 300
        fuse_left_port_disp = 0
        fuse_right_port_disp = 0

        name = f"fuselage_" + str(self.cursor.substructures['fuselage'] + 1)

        fuselage = self.designer.add_fuselage(name=name,
                                        length=fuse_length,
                                        sphere_diameter=fuse_sphere_diameter,
                                        middle_length=fuse_middle_length,
                                        tail_diameter=fuse_tail_diameter,
                                        floor_height=fuse_floor_height,
                                        seat_1_fb=fuse_seat_1_fb,
                                        seat_1_lr=fuse_seat_1_lr,
                                        seat_2_fb=fuse_seat_2_fb,
                                        seat_2_lr=fuse_seat_2_lr,
                                        top_port_disp=fuse_top_port_disp,
                                        bottom_port_disp=fuse_bottom_port_disp,
                                        left_port_disp=fuse_left_port_disp,
                                        right_port_disp=fuse_right_port_disp)
        
        if orig_inst is not None and orig_conn is not None:
            # parameters describe an instance and connector to attach the new fuselage onto
            # possibly also overriding the destination connector on the newly created fuselage instance
            self.designer.connect(orig_inst, orig_conn, fuselage, dest_conn)

        self.cursor.substructures['fuselage'] += 1

        return fuselage, name

    def build_minimal(self):
        """ the base design contains a fuselage with 2 large wings on either side and
            a rail extending from the rear of the fuselage and the top of the fuselage"""

        fuselage, fuselage_name = self.make_fuselage()

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

        right_wing = self.designer.add_wing(name=f"{fuselage_name}_right_wing",
                                naca=wing_naca,
                                chord=wing_chord,
                                span=wing_span,
                                load=wing_load,
                                left_inst=fuselage,
                                left_conn="RIGHT_CONNECTOR")

        left_wing = self.designer.add_wing(name=f"{fuselage_name}_left_wing",
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

        # todo, consider returning these instances as well or randomizing the connector locations
        brr, _, _ = self.make_rail(start_inst=fuselage, start_conn="REAR_CONNECTOR", is_base_rail=True, name="base_rail_rear", alt_orig_cyl_connector="TOP_CONNECTOR")
        brt, _, _ = self.make_rail(start_inst=fuselage, start_conn="TOP_CONNECTOR", is_base_rail=True, name="base_rail_top", alt_orig_cyl_connector="TOP_CONNECTOR")
        brb, _, _= self.make_rail(start_inst=fuselage, start_conn="BOTTOM_CONNECTOR", is_base_rail=True, name="base_rail_bottom", alt_orig_cyl_connector="TOP_CONNECTOR")

        self.make_rail(start_inst=brt[0], start_conn="FRONT_CONNECTOR", is_base_rail=False, name="base_rail_top_cross")
        self.make_rail(start_inst=brb[0], start_conn="FRONT_CONNECTOR", is_base_rail=False, name="base_rail_bottom_cross")
        self.make_rail(start_inst=brr[0], start_conn="BOTTOM_CONNECTOR", is_base_rail=False, name="base_rail_rear_top_prong")

        return fuselage, battery_controller

    def make_cylinder_on_wing_nacaport():
        """ given the wing instance and connection"""
        pass


    def run_design(self, design_name):
        print(f"running design")
        workflow = "uam_direct2cad"
        self.architect = Architect()
        self.architect.open_jenkins_client(workflow)
        self.architect.update_parameters("graphGUID", design_name)
        self.architect.update_parameters("paramFile", "study_params_NewAxe.csv")
        
        self.build = self.architect.jenkins_client.build_and_wait(
            workflow, self.architect.jenkins_parameters)
        
        self.architect.jenkins_client.save_results_from_build(
            self.build,
            design_name,
        )

        self.architect.open_query_client()
        #result_name = design_name + "_" + str(int(self.build.number))
        self.design_json = self.architect.client.get_design_data(design_name)
        self.architect.jenkins_client.add_design_json_to_results(
            design_name + "_" + str(int(self.build.number)), self.design_json)
        
        self.architect.jenkins_client.grab_extra_jsons_direct2cad(design_name)
        
        self.architect.close_client()
        

def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--spec", action='store_true', help="create designs from a specfile")
    parser.add_argument("--specfile", type=str, default=None, help="filepath to the json containing vehicle descriptions")
    parser.add_argument("--random", action='store_true', help="create random designs")
    parser.add_argument("--n", type=int, default=200, help="the number of designs to build")

    args = parser.parse_args(args)
    from_spec = args.spec
    specfile = args.specfile
    randm = args.random
    num_designs = args.n        

    sb = StringerBuilder("C:\\stringer\\100_designs.txt")
    # also 100_designs_td5310_cs13.txt where tdxyzw is token distribution is csxy is cluster size range
    if randm:
        print("random builder loop")
        sb.run_builder_loop(num_designs=num_designs)
    elif from_spec:
        print("spec builder loop")
        assert os.path.exists(specfile), f"specfile {specfile} does not exist"
        sb.run_builder_loop(build_from_spec=from_spec, spec_filepath=specfile)

if __name__ == '__main__':
    run()