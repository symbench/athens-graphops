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

from typing import Any, Dict, List
import json
import os
import sys

from gremlin_python.driver import client as gremlin_client

from . import HOSTNAME, SCRIPTS


class Client():
    def __init__(self, host: str, timeout: float = 10000):
        self.addr = "ws://{}:8182/gremlin".format(host)
        self.client = gremlin_client.Client(self.addr, "g")
        sys.stderr.write("Connected to {}\n".format(self.addr))
        self.timeout = timeout

    def close(self):
        if self.client:
            sys.stderr.write("Closed connection\n")
            self.client.close()
            self.client = None

    def submit_query(self, query: str) -> Any:
        result = self.client.submit(
            query, request_options={'evaluationTimeout': self.timeout})
        result = result.all().result()
        return result

    def submit_script(self, script: str, **params) -> List[Any]:
        filename = os.path.join(SCRIPTS, script + ".groovy")
        results = []
        with open(filename, "r") as file:
            for query in file:
                query = query.strip()
                if not query:
                    continue
                for var, val in params.items():
                    query = query.replace(var, str(val))
                results.append(self.submit_query(query))
        return results

    def get_design_list(self) -> List[str]:
        results = self.submit_script("info_designList")
        return sorted(results[0])

    def get_component_map(self, design: str) -> List[Dict[str, Any]]:
        results = self.submit_script("info_componentMap",
                                     __SOURCEDESIGN__=design)
        return sorted(results[0], key=lambda x: x["FROM_COMP"])

    def get_connection_map(self, design: str) -> List[Dict[str, Any]]:
        results = self.submit_script("info_connectionMap",
                                     __SOURCEDESIGN__=design)
        return sorted(results[0], key=lambda x: (x["FROM_COMP"], x["TO_COMP"]))

    def get_parameter_map(self, design: str) -> List[Dict[str, Any]]:
        results = self.submit_script("info_paramMap",
                                     __SOURCEDESIGN__=design)
        return sorted(results[0], key=lambda x: (
            (x["COMPONENT_NAME"], x["COMPONENT_PARAM"])))

    def get_component_data(self, component: str) -> Dict[str, Any]:
        pass

    def get_instance_data(self, design: str, component: str) -> Dict[str, Any]:
        pass


def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--host', type=str, metavar='IP', default=HOSTNAME,
                        help="sets the host address of the gremlin database")
    parser.add_argument('--list', action='store_true',
                        help="prints all design names")
    parser.add_argument('--design', metavar='NAME',
                        help="prints the components of the given design")
    args = parser.parse_args(args)

    client = Client(host=args.host)

    if args.list:
        data = client.get_design_list()
        print(json.dumps({
            "designs": data
        }, indent=2))

    if args.design:
        components = client.get_component_map(args.design)
        connections = client.get_connection_map(args.design)
        parameters = client.get_parameter_map(args.design)
        print(json.dumps({
            "design": args.design,
            "components": components,
            "connections": connections,
            "parameters": parameters,
        }, indent=2))

    client.close()


if __name__ == '__main__':
    run()
