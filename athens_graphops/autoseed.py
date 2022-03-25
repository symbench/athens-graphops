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

from typing import Any, Dict, List, Optional

import importlib
import json
import os
import tempfile

from . import CONFIG
from . import query


def import_autoseed():
    spec = importlib.util.spec_from_file_location(
        "autoseed",
        os.path.join(CONFIG["batch_dirs"][-1], "AutoSeed.py"))
    autoseed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(autoseed)
    return autoseed


def autoseed(design: str, filename: str):
    filename = os.path.abspath(filename)
    newname = os.path.splitext(os.path.basename(filename))[0]

    client = query.Client()

    if design not in client.get_design_names():
        print("Desgin {} not found".format(design))
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
    print("Copying file {} to {}".format(ifilename, filename))
    with open(ifilename, "r") as ifile:
        with open(filename, "w") as ofile:
            ofile.write(ifile.read())


def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('design', help="name of the design")
    parser.add_argument('--output', metavar="CSV", help="output CSV filename")
    args = parser.parse_args(args)

    if not args.output:
        args.output = args.design + ".csv"

    autoseed(design=args.design, filename=args.output)


if __name__ == '__main__':
    run()
