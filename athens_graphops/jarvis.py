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
import os
import json
import argparse
import zipfile
import re
from io import TextIOWrapper, BytesIO
from csv import DictReader


from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from dotenv import load_dotenv


def cherry_pick(data_zip):
    results = []
    re_design = re.compile(
        r'<node id="[^"]+"><data key="labelV">\[avm\]Design</data>'
        r'<data key="\[\]Name">([^<]+)</data>'
    )

    with zipfile.ZipFile(data_zip) as f_zip:
        with f_zip.open("namedGraph.graphml") as f_graphml:
            design_names = re_design.findall(f_graphml.read().decode("utf-8"))
            if not design_names or len(design_names) > 1:
                raise ValueError(
                    "No design found or more than one design found:"
                    f"{design_names}"
                )
            design_name = design_names[0]

        with f_zip.open("output.csv", "r") as f_csv:
            for output in DictReader(TextIOWrapper(f_csv, "utf-8")):

                guid = output["GUID"]

                with f_zip.open(f"archive/{guid}/uav_gen.stl") as f_stl:
                    stl_file = BytesIO(f_stl.read())

                results.append(
                    {
                        "name": design_name,
                        "is_rejected": (
                            output["AnalysisError"].upper() == "FALSE"
                        ),
                        "mass_kg": float(output["mass"]),
                        "requested_lateral_speed": int(
                            output["Requested_Lateral_Speed"]
                        ),
                        "stl_file": stl_file,
                    }
                )

    return results


def jarvis_upload(designs, jarvis_url, jarvis_auth):
    design_query = gql(
        """
mutation designsGenerateMany($designs: [UAVDesignCreateInput!]!) {
  createUavDesigns(input: $designs) {
    uavDesigns {
      id
    }
  }
}
"""
    )

    file_query = gql(
        """
mutation(
  $file: Upload!
  $team_name: TeamName!
  $challenge_name: ChallengeName!
  $jarvis_design_id: ID!
) {
  uploadFile(
    file: $file
    challenge_name: $challenge_name
    team_name: $team_name
    jarvis_design_id: $jarvis_design_id
  ) {
    url
  }
}
"""
    )

    transport = AIOHTTPTransport(
        jarvis_url, headers={"Authorization": jarvis_auth}
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    for design in designs:
        design_params = {k: v for k, v in design.items() if k != "stl_file"}
        result = client.execute(
            design_query, variable_values={"designs": design_params}
        )

        design_id = result["createUavDesigns"]["uavDesigns"][0]["id"]

        file_params = {
            "team_name": design["team_name"],
            "challenge_name": "UAV",
            "jarvis_design_id": design_id,
            "file": design["stl_file"],
        }
        result = client.execute(
            file_query, variable_values=file_params, upload_files=True
        )
        print(f"Uploaded {design['name']} as {design_id}")


def run(args=None):
    load_dotenv()

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "data.zip", help="a data.zip file from the uam_direct2cad workflow"
    )
    parser.add_argument(
        "--jarvis-url",
        default=os.environ.get("JARVIS_URL"),
        help="JARVIS URL (you can put this in .env",
    )
    parser.add_argument(
        "--jarvis-auth",
        default=os.environ.get("JARVIS_AUTH"),
        help="JARVIS auth token (you can put this in .env",
    )
    parser.add_argument(
        "--team",
        default="VANDERBILT",
        help="Team name",
    )
    args = parser.parse_args(args)

    results = cherry_pick(getattr(args, "data.zip"))
    designs = [{**result, "team_name": args.team} for result in results]
    jarvis_upload(designs, args.jarvis_url, args.jarvis_auth)


if __name__ == "__main__":
    run()
