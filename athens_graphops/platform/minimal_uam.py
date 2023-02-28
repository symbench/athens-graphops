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
#
#===============================================================================
# UAM Design
# Key Design Feature: Minimal design elements

from ..designer import Designer, StudyParam

# Cargo case attached but empty


def create_minimal_uam():
    return minimal_platform("")


def minimal_platform(variant):
    corpus_type = "UAM"
    description = "Study Parameters for Minimal Platform direct2cad Run"
    design_name = "MinimalUAM" + variant

    designer = Designer()
    designer.create_design(design_name)

    ########################################
    # Static params

    ########################################
    # Tunable params
    fuse_length = designer.set_study_param("fuse_length", 2000)
    fuse_sphere_diameter = designer.set_study_param(
        "fuse_sphere_diameter", 1520)
    fuse_middle_length = designer.set_study_param("fuse_middle_length", 300)
    fuse_tail_diameter = designer.set_study_param("fuse_tail_diameter", 200)
    fuse_floor_height = designer.set_study_param("fuse_floor_height", 150)
    seat1_fb_pos = designer.set_study_param("seat1_fb_pos", 1000)
    seat1_lr_pos = designer.set_study_param("seat1_lr_pos", -210)
    seat2_fb_pos = designer.set_study_param("seat2_fb_pos", 1000)
    seat2_lr_pos = designer.set_study_param("seat2_lr_pos", 210)

    ########################################
    # Center (Fuselage)
    designer.add_fuselage_uam(name="fuselage",
                              length=fuse_length,
                              sphere_diameter=fuse_sphere_diameter,
                              middle_length=fuse_middle_length,
                              tail_diameter=fuse_tail_diameter,
                              floor_height=fuse_floor_height,
                              seat_1_fb=seat1_fb_pos,
                              seat_1_lr=seat1_lr_pos,
                              seat_2_fb=seat2_fb_pos,
                              seat_2_lr=seat2_lr_pos)

    designer.close_design(corpus="uam")

    study_params = [
        StudyParam("Flight_Path", 9, "FDM"),
        StudyParam("Requested_Lateral_Speed", 23, "FDM"),
        StudyParam("Requested_Vertical_Speed", -5, "FDM"),
        StudyParam("Requested_Vertical_Down_Speed", 5, "FDM"),
        StudyParam("Requested_Lateral_Acceleration", 2, "FDM"),
        StudyParam("Requested_Lateral_Deceleration", -3, "FDM"),
        StudyParam("Requested_Vertical_Acceleration", -1, "FDM"),
        StudyParam("Requested_Vertical_Deceleration", 1, "FDM"),
        # James suggested not to tweak these
        # StudyParam("Landing_Approach_Height", 3, "FDM"),
        # StudyParam("Vertical_Landing_Speed", 0.5, "FDM"),    # not used in buildcad.py
        # StudyParam("Vertical_Landing_Speed_At_Ground", 0.1, "FDM"),
        StudyParam("Q_Position", 1, "FDM"),
        StudyParam("Q_Velocity", 0.5, "FDM"),
        StudyParam("Q_Angular_Velocity", 1, "FDM"),
        StudyParam("Q_Angles", 0.5, "FDM"),
        StudyParam("Ctrl_R", 0.25, "FDM"),
    ]

    # Add all study parameters automatically
    for val in locals().values():
        if isinstance(val, StudyParam):
            study_params.append(val)

    return design_name, description, corpus_type, study_params
