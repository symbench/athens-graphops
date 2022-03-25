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
import json
import os
import sys

from gremlin_python.driver import client as gremlin_client

from . import CONFIG


class Client():
    def __init__(self,
                 host: Optional[str] = None,
                 timeout: Optional[float] = None):
        if host is None:
            host = CONFIG["hostname"]
        self.addr = "ws://{}:8182/gremlin".format(host)

        self.client = gremlin_client.Client(self.addr, "g")
        sys.stderr.write("Connected to {}\n".format(self.addr))

        if timeout is None:
            timeout = CONFIG["timeout"]
        self.timeout = timeout * 1000

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
        for dir in CONFIG["script_dirs"]:
            filename = os.path.join(dir, script)
            if os.path.exists(filename):
                break
        else:
            raise ValueError("sciprt {} not found".format(script))

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
        results = self.submit_script("info_designList.groovy")
        return sorted(results[0])

    def get_component_list(self, design: str) -> List[Dict[str, Any]]:
        results = self.submit_script("info_componentMap.groovy",
                                     __SOURCEDESIGN__=design)
        return sorted(results[0], key=lambda x: x["FROM_COMP"])

    def get_connection_list(self, design: str) -> List[Dict[str, Any]]:
        results = self.submit_script("info_connectionMap.groovy",
                                     __SOURCEDESIGN__=design)
        return sorted(results[0], key=lambda x: (x["FROM_COMP"], x["TO_COMP"]))

    def get_parameter_list(self, design: str) -> List[Dict[str, Any]]:
        results = self.submit_script("info_paramMap.groovy",
                                     __SOURCEDESIGN__=design)
        return sorted(results[0], key=lambda x: (
            (x["COMPONENT_NAME"], x["COMPONENT_PARAM"])))

    def get_old_corpus_list(self) -> List[Dict[str, Any]]:
        results = self.submit_script("info_corpusComponents.groovy")
        return sorted(results[0], key=lambda x: (
            x["Classification"], x["Component"]))

    def get_corpus_list(self) -> List[Dict[str, Any]]:
        results = self.submit_script("corpus_list.groovy")
        return results[0]

    def get_property_table(self, classification: str) -> List[Dict[str, Any]]:
        results = self.submit_script("property_table.groovy",
                                     __CLASSIFICATION__=classification)
        return results[0]

    def get_corpus_parameters(self, classification: str) -> Dict[str, Any]:
        pass


def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--list', action='store_true',
                        help="prints all design names")
    parser.add_argument('--old-corpus', action='store_true',
                        help="prints all component types")
    parser.add_argument('--corpus', action='store_true',
                        help="prints all component types")
    parser.add_argument('--property-table', metavar='CLASS',
                        help="prints the property table for the given class")
    parser.add_argument('--design', metavar='NAME',
                        help="prints the components of the given design")
    parser.add_argument('--raw', metavar='QUERY',
                        help="executes the given raw query string")
    parser.add_argument('--script', metavar='FILE',
                        help="executes the given script query")
    args = parser.parse_args(args)

    client = Client()

    if args.list:
        data = client.get_design_list()
        print(json.dumps(data, indent=2, sort_keys=True))

    if args.old_corpus:
        data = client.get_old_corpus_list()
        print(json.dumps(data, indent=2, sort_keys=True))

    if args.corpus:
        data = client.get_corpus_list()
        print(json.dumps(data, indent=2, sort_keys=True))

    if args.property_table:
        data = client.get_property_table(args.property_table)
        print(json.dumps(data, indent=2, sort_keys=True))

    if args.design:
        components = client.get_component_list(args.design)
        connections = client.get_connection_list(args.design)
        parameters = client.get_parameter_list(args.design)
        print(json.dumps({
            "design": args.design,
            "components": components,
            "connections": connections,
            "parameters": parameters,
        }, indent=2, sort_keys=True))

    if args.raw:
        print(client.submit_query(args.raw))

    if args.script:
        results = client.submit_script(args.script)
        for result in results:
            print(result)

    client.close()


if __name__ == '__main__':
    run()
