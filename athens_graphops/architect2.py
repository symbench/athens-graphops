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

# This is Peter's sandbox for Hackathon 2

import sys
import inspect
from csv import DictWriter
from collections.abc import Sequence

def write_study_params(design_name, params):
    study_filename = f"{design_name}_study.csv"

    param_runs = [len(v) for v in params.values() if isinstance(v, Sequence)]
    if param_runs:
        n_studies = max(param_runs)
    else:
        n_studies = 1

    full_params = {}
    for p_name in params:
        if isinstance(params[p_name], Sequence):
            if len(params[p_name]) != n_studies:
                raise ValueError(
                    f"Parameter {p_name} has {len(params[p_name])} values, "
                    f"but {n_studies} values are expected."
                )
            full_params[p_name] = params[p_name]
        else:
            full_params[p_name] = [params[p_name]] * n_studies

    with open(study_filename, "w", newline="") as study_file:
        writer = DictWriter(study_file, fieldnames=full_params.keys())
        writer.writeheader()
        for i in range(n_studies):
            writer.writerow({k: v[i] for k, v in full_params.items()})

    print(f"Study parameters written to {study_filename}.")


def run(args=None):
    import argparse
    from .architect2_designs import designs  # avoid circular import

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "design",
        choices=designs.keys(),
        default=next(iter(designs)),
        nargs="?",
    )

    args = parser.parse_args(args)
    designs[args.design]()


if __name__ == "__main__":
    run()
