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

        # memoize
        self.model_to_class = dict()

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
            lines = list(file.readlines())
            lines.append("")

            query = ""
            for line in lines:
                line = line.rstrip()
                if line.strip().startswith("//"):
                    continue
                if line.startswith(" ") or line.startswith("\t"):
                    query += "\n" + line
                    continue

                if query:
                    for var, val in params.items():
                        query = query.replace(var, str(val))
                    # print(query)
                    results.append(self.submit_query(query))

                query = line
            assert query == ""

        return results

    def get_design_names(self) -> List[str]:
        results = self.submit_script("info_designList.groovy")
        return sorted(results[0])

    def get_component_map(self, design: str) -> List[Dict[str, Any]]:
        results = self.submit_script("info_componentMap.groovy",
                                     __SOURCEDESIGN__=design)
        return sorted(results[0], key=lambda x: x["FROM_COMP"])

    def get_connection_map(self, design: str) -> List[Dict[str, Any]]:
        results = self.submit_script("info_connectionMap.groovy",
                                     __SOURCEDESIGN__=design)
        return sorted(results[0], key=lambda x: (x["FROM_COMP"], x["TO_COMP"]))

    def get_parameter_map(self, design: str) -> List[Dict[str, Any]]:
        results = self.submit_script("info_paramMap.groovy",
                                     __SOURCEDESIGN__=design)
        return sorted(results[0], key=lambda x: (
            (x["COMPONENT_NAME"], x["COMPONENT_PARAM"])))

    def get_corpus_components(self) -> List[Dict[str, Any]]:
        results = self.submit_script("info_corpusComponents.groovy")
        return sorted(results[0], key=lambda x: (
            x["Classification"], x["Component"]))

    def get_design_data(self, design: str) -> List[Dict[str, Any]]:
        results = self.submit_script("design_data.groovy",
                                     __SOURCEDESIGN__=design)
        return results[0]

    def get_corpus_data(self) -> List[Dict[str, Any]]:
        results = self.submit_script("corpus_data.groovy")
        return results[0]

    def get_corpus_model(self, model: str) -> Dict[str, Any]:
        results = self.submit_script("corpus_model.groovy",
                                     __MODELNAME__=model)
        return results[0]

    def get_property_table(self, classification: str) -> List[Dict[str, Any]]:
        results = self.submit_script("property_table.groovy",
                                     __CLASSIFICATION__=classification)
        return results[0]

    def delete_design(self, design: str):
        self.submit_script("clearDesign.groovy", __DESTDESIGN__=design)

    def create_design(self, design: str):
        self.submit_script("clearDesign.groovy", __DESTDESIGN__=design)
        self.submit_script("addBlankDesign.groovy", __DESTDESIGN__=design)

    def get_model_class(self, model: str) -> str:
        if model in self.model_to_class:
            return self.model_to_class[model]

        results = self.submit_script("get_model_class.groovy",
                                     __MODELNAME__=model)
        if results[0]:
            class_name = results[0][0]
        else:
            class_name = model
        self.model_to_class[model] = class_name
        return class_name

    def create_instance(self, design: str, model: str, instance: str):
        class_name = self.get_model_class(model)
        self.submit_script("cloneCIOpt.groovy",
                           __SOURCEDESIGN__="AllComponentsUAM",
                           __SOURCENAME__=class_name,
                           __DESTDESIGN__=design,
                           __DESTNAME__=instance)
        if model != class_name:
            self.submit_script("swap.groovy",
                               __DESIGN__=design,
                               __COMPONENT_INSTANCE__=instance,
                               __NEW_COMPONENT__=model)

    def create_connection(self, design: str,
                          instance1: str, connector1: str,
                          instance2: str, connector2: str):
        """
        Make sure to connect the two instances only once in any direction!
        """
        self.submit_script("addConn.groovy",
                           __SOURCEDESIGN__=design,
                           __SOURCECOMP__=instance1,
                           __SOURCECONN__=connector1,
                           __DESTCOMP__=instance2,
                           __DESTCONN__=connector2)

    def create_parameter(self, design: str, parameter: str, value: str):
        upper = parameter.upper()
        if any([upper.find(item) != 1 for item in
                ["LENG", "RADI", "OFFSET", "POSIT", "LEGS"]]):
            script = 'addNewPropMM.groovy'
        else:
            script = 'addNewPropx.groovy'
        self.submit_script(script,
                           __SOURCEDESIGN__=design,
                           __PROPNAME__=parameter,
                           __PROPVAL__=value)

    def assign_parameter(self, design: str, instance: str, model_param: str, parameter: str):
        self.submit_script('addPropConnl.groovy',
                           __SOURCEDESIGN__=design,
                           __DESTCOMP__=instance,
                           __DESTPI__=model_param,
                           __SOURCEPROP__=parameter)

    def orient_design(self, design: str, instance: str):
        self.submit_script('addRefCoordSysx.groovy',
                           __SOURCEDESIGN__=design,
                           __ORIENTNAME__=instance)


def run(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--design-names', action='store_true',
                        help="prints all design names")
    parser.add_argument('--design-data', metavar='NAME',
                        help="prints the components of the given design")
    parser.add_argument('--corpus-data', action='store_true',
                        help="prints all component models")
    parser.add_argument('--corpus-model', metavar='MOD',
                        help="prints a single component model")
    parser.add_argument('--property-table', metavar='CLS',
                        help="prints the property table for a component class")
    parser.add_argument('--raw', metavar='QUERY',
                        help="executes the given raw query string")
    parser.add_argument('--script', metavar='FILE',
                        help="executes the given groovy script query")
    parser.add_argument('--params', metavar="X", nargs="*", default=[],
                        help="use this parameter list for scripts")
    parser.add_argument('--delete-design', metavar='NAME',
                        help="deletes the given design")
    args = parser.parse_args(args)

    if len(args.params) % 2 != 0:
        raise ValueError("Number of parameters must be even.")

    params = {}
    for i in range(0, len(args.params), 2):
        params[args.params[i]] = args.params[i+1]

    client = Client()

    if args.design_names:
        data = client.get_design_names()
        print(json.dumps(data, indent=2, sort_keys=True))

    if args.design_data:
        data = client.get_design_data(design=args.design_data)
        print(json.dumps(data, indent=2, sort_keys=True))

    if args.corpus_data:
        data = client.get_corpus_data()
        print(json.dumps(data, indent=2, sort_keys=True))

    if args.corpus_model:
        data = client.get_corpus_model(model=args.corpus_model)
        print(json.dumps(data, indent=2, sort_keys=True))

    if args.property_table:
        data = client.get_property_table(args.property_table)
        print(json.dumps(data, indent=2, sort_keys=True))

    if args.raw:
        print(client.submit_query(args.raw))

    if args.script:
        results = client.submit_script(args.script, **params)
        for result in results:
            print(result)

    if args.delete_design:
        client.delete_design(args.delete_design)

    client.close()


if __name__ == '__main__':
    run()
