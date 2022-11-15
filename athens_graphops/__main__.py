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

import argparse
import sys

from . import CONFIG
from . import batch
from . import dataset
from . import query
from . import validate
from . import designer
from . import architect
from . import factory
from . import workflow


def run():
    # hack the subcommands
    commands = [
        "autograph",
        "autoseed",
        "dataset",
        "query",
        "validate",
        "designer",
        "architect",
        "factory",
        "workflow",
        "update"
    ]
    pos = len(sys.argv)
    for cmd in commands:
        if cmd in sys.argv:
            pos = sys.argv.index(cmd) + 1

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--host', type=str, metavar='IP',
                        help="sets the host address of the gremlin database")
    parser.add_argument('--timeout', type=float, metavar='SEC',
                        help="sets the timeout in seconds for each query")
    parser.add_argument('--jenkinsuser', type=str, metavar='user',
                        help="sets the Jenkins username for workflow runs")
    parser.add_argument('--jenkinspwd', type=str, metavar='pwd',
                        help="sets the Jenkins password for workflow runs")
    parser.add_argument(
        'command', help="subcommand to execute",
        choices=sorted(commands))
    args = parser.parse_args(sys.argv[1:pos])

    # hack the program name for nested parsers
    sys.argv[0] += ' ' + args.command
    args.command = args.command.replace('_', '-')

    # hack the global config
    if args.host:
        CONFIG["hostname"] = args.host
    if args.timeout:
        CONFIG["timeout"] = args.timeout
    if args.jenkinsuser:
        CONFIG["jenkinsuser"] = args.jenkinsuser
    if args.jenkinspwd:
        CONFIG["jenkinspwd"] = args.jenkinspwd

    if args.command == "query":
        query.run(args=sys.argv[pos:])
    elif args.command == "validate":
        validate.run(args=sys.argv[pos:])
    elif args.command == "autograph":
        batch.run_autograph(args=sys.argv[pos:])
    elif args.command == "autoseed":
        batch.run_autoseed(args=sys.argv[pos:])
    elif args.command == "dataset":
        dataset.run(args=sys.argv[pos:])
    elif args.command == "designer":
        designer.run(args=sys.argv[pos:])
    elif args.command == "architect":
        architect.run(args=sys.argv[pos:])
    elif args.command == "factory":
        factory.run(args=sys.argv[pos:])
    elif args.command == "workflow":
        workflow.run(args=sys.argv[pos:])
    elif args.command == "update":
        batch.run_update_design(args=sys.argv[pos:])
    else:
        parser.print_help()


if __name__ == '__main__':
    run()
