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
#
#===============================================================================
# These functions are involved in exporting design data.  
# Autoseed and Autograph pull directly from the JanusGraph database.

import ssl
from typing import Any, List

import importlib.util
import json
import os
import tempfile
import shutil

from . import CONFIG
from . import query


def import_autoseed():
    spec = importlib.util.spec_from_file_location(
        "autoseed",
        os.path.join(CONFIG["batch_dirs"][-1], "autoseed2.py"))
    autoseed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(autoseed)
    return autoseed


def autograph(batchfile: str) -> List[Any]:
    for dir in CONFIG["batch_dirs"]:
        filename = os.path.join(dir, batchfile)
        if os.path.exists(filename):
            break
    else:
        raise ValueError("batchfile {} not found".format(batchfile))

    all_results = []
    client = query.Client()

    print("Reading {}".format(filename))
    with open(filename) as file:
        for line in file:
            param_list = line.strip().split(',')
            if param_list[0] in ['\ufeffQtemplate', 'Qtemplate']:
                continue

            printout = [param_list[0]]
            param_dict = dict()
            for i in range(1, len(param_list), 2):
                if param_list[i]:
                    param_dict[param_list[i]] = param_list[i+1]
                    printout.extend(param_list[i:i+2])

            print("Executing {}".format(", ".join(printout)))
            results = client.submit_script(
                param_list[0] + ".groovy", **param_dict)
            all_results.extend(results)
            for result in results:
                if result:
                    print(result)

    client.close()
    return all_results


def autoseed(design: str, batchfile: str):
    print("Dumping {} to {}".format(design, batchfile))

    batchfile = os.path.abspath(batchfile)
    newname = os.path.splitext(os.path.basename(batchfile))[0]

    client = query.Client()

    if design not in client.get_design_names():
        print("Design {} not found".format(design))
        client.close()
        return

    print("Importing autoseed module")
    autoseed = import_autoseed()

    tempdir = tempfile.TemporaryDirectory(prefix="athens_graphops_")

    for idx, script in enumerate([
            "info_paramMap",
            "info_componentMap",
            "info_connectionMap",
            "info_corpusComponents"]):
        fname = os.path.join(tempdir.name,
                             "{}{}.json".format(script, idx+1))
        print("Generating {}".format(fname))
        if script == "info_corpusComponents":
            script = "better_" + script
        result = client.submit_script(script + ".groovy",
                                      __SOURCEDESIGN__=design)
        with open(fname, "w") as file:
            json.dump(result[0], file)

    client.close()

    print("Running autoseed {}".format(newname))
    olddir = os.getcwd()
    os.chdir(tempdir.name)
    autoseed.genAutographScript(newname, dst_folder=tempdir.name)
    os.chdir(olddir)

    ifilename = os.path.join(tempdir.name, newname + ".csv")
    print("Copying file {} to {}".format(ifilename, batchfile))
    with open(ifilename, "r") as ifile:
        with open(batchfile, "w") as ofile:
            ofile.write(ifile.read())

# MM TODO:  Keep???
def update_design(design_folder: str, design: str):
    """ 
    Update a design graph to match the parameters indicated in the 
    designParameter.json file. 

    In parameter exploration, the designParameter.json file is updated 
    and the tools run to explore the design space. Some designs will 
    result in solutions that may be explored or analyzed future. This 
    function will take the results data.zip file folder contents (with
    modified designParameter.json files and create a new version of the 
    design in the Janusgraph with the updated parameter values.

    The design folder should be an absolute path. The design name can be the same as before or new.

    Input jsons needed (found in top directory of data.zip file):
    - info_paramMap4.json
    - info_componentMapList1.json
    - info_connectionMap6.json

    Need to create:
    - info_corpusComponents4.json

    Steps taken:
    1) Check if input json files are available
    2) Update info_paramMap4.json from data.zip file - archive/result_1/designParam.json
    3) Create the .csv file to create a design (using autoseed)
    4) run autograph to create design in Janusgraph DB
    5) re-create the <design name>_design_data.json file (prove change reflected in graph)
    """
    print("Updating {} design graph".format(design))
    client = query.Client()

    # Make sure result folder includes needed input json files which
    # describe the design and translate names to autoseed expected filenames
    jsons_available = True
    paramMap_filename_src = os.path.join(design_folder, 'info_paramMap4.json')
    paramMap_filename_dest = os.path.join(design_folder, 'info_paramMap1.json')
    if os.path.isfile(paramMap_filename_src):
        try:
            with open(paramMap_filename_src, 'r') as pfile:
                paramMap = json.load(pfile)
        except:
            print("failed to load {}".format(paramMap_filename_src))
            jsons_available = False
    else:
        print("Missing {} file".format(paramMap_filename_src))
        jsons_available = False

    connMap_filename_src = os.path.join(
        design_folder, 'info_connectionMap6.json')
    connMap_filename_dest = os.path.join(
        design_folder, 'info_connectionMap3.json')
    if os.path.isfile(connMap_filename_src):
        shutil.copyfile(connMap_filename_src, connMap_filename_dest)
    else:
        print("Missing {} file".format(connMap_filename_src))
        jsons_available = False

    compMap_filename_src = os.path.join(
        design_folder, 'info_componentMapList1.json')
    compMap_filename_dest = os.path.join(
        design_folder, 'info_componentMap2.json')
    if os.path.isfile(compMap_filename_src):
        shutil.copyfile(compMap_filename_src, compMap_filename_dest)
    else:
        print("Missing {} file".format(compMap_filename_src))
        jsons_available = False

    designParams_filename = os.path.join(
        design_folder, "archive/result_1/designParameters.json")
    if os.path.isfile(designParams_filename):
        try:
            with open(designParams_filename, 'r') as dfile:
                designParams = json.load(dfile)
        except:
            print("failed to load {}".format(designParams_filename))
            jsons_available = False
    else:
        print("Missing {} file".format(designParams_filename))
        jsons_available = False

    # Create info_corpusComponents.json
    corpus_fname = os.path.join(design_folder, "info_corpusComponents4.json")
    result = client.submit_script("better_info_corpusComponents.groovy",
                                  __SOURCEDESIGN__=design)
    with open(corpus_fname, "w") as file:
        json.dump(result[0], file)

    if jsons_available:
        # If design already exists in the graph database, remove it
        names = client.get_design_names()
        print("Available Designs: {}".format(names))
        if design in names:
            client.delete_design(design)
            print("Design {} found, deleted the design".format(design))

        # Make sure parameters in info_paramMap1.json are up to date with the design parameters
        # file found in archive/result_1/designParam.json
        for param in paramMap:
            component = param["COMPONENT_NAME"]
            designParam_comp = designParams.get(component)
            param_name = param["COMPONENT_PARAM"].upper()
            if param_name in designParam_comp:
                if param_name == "NACA_PROFILE":
                    param_val = str(
                        int(designParam_comp[param_name])).rjust(4, "0")
                else:
                    param_val = designParam_comp[param_name]
                param["DESIGN_PARAM_VAL"] = str(param_val)
                print("*****designParam: {}, paramMap: {}".format(
                    designParam_comp[param_name], param["DESIGN_PARAM_VAL"]))
            else:
                print("Parameter name not found in designParameters.json")

        # Save updated paramMap in current file and file needed for autoseed
        with open(paramMap_filename_src, "w") as pfile_src:
            json.dump(paramMap, pfile_src)
        with open(paramMap_filename_dest, "w") as pfile_dest:
            json.dump(paramMap, pfile_dest)

        # Autograph opens a new client, so close here
        client.close()

        # Create build instruction csv file for the design
        print("Importing autoseed module")
        autoseed = import_autoseed()

        print("Running autoseed {}".format(design))
        current_dir = os.getcwd()
        os.chdir(design_folder)
        autoseed.genAutographScript(design, dst_folder=design_folder)
        os.chdir(current_dir)

        # Create design in graph DB
        autoseed_outputfile = os.path.join(design_folder, design + ".csv")
        autograph(autoseed_outputfile)

        # Remove files created for autoseed
        # os.remove(connMap_filename_dest)
        # os.remove(compMap_filename_dest)
        # os.remove(paramMap_filename_dest)
        # os.remove(corpus_fname)

        # Recreate design_data file for the design
        # Open up the query client again to pull a new design data json
        newClient = query.Client()
        design_json = newClient.get_design_data(design)
        designdata_file = os.path.join(
            design_folder, design + "_design_data.json")
        with open(designdata_file, "w") as file:
            json.dump(design_json, file)
        newClient.close()


def run_autograph(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('file', help="a .csv batch file to run")
    args = parser.parse_args(args)

    autograph(batchfile=args.file)


def run_autoseed(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('file', help="a .csv batch file to be created")
    parser.add_argument('--name', help="design name to be dumped")
    args = parser.parse_args(args)

    if os.path.splitext(args.file)[1] != ".csv":
        args.file += ".csv"

    if args.name is None:
        args.name = os.path.splitext(os.path.basename(args.file))[0]

    autoseed(design=args.name, batchfile=args.file)


def run_update_design(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        'folder', help="an unzipped result folder with updated design")
    parser.add_argument('--name', help="design name to be updated")
    args = parser.parse_args(args)

    if os.path.isdir(args.folder):
        # If design name is the same as the results folder, no need to identify
        if args.name is None:
            args.name = os.path.splitext(os.path.basename(args.file))[0]

        update_design(design_folder=args.folder, design=args.name)
    else:
        print("Design Folder {} not found. Please indicate the results folder with design to update in the graph DB".format(args.folder))


if __name__ == '__main__':
    run_autograph()
