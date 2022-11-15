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

import time
from csv import DictWriter
from collections.abc import Sequence
from itertools import chain


from minio import Minio
from api4jenkins import Jenkins


def write_study_params(design_name, params):
    study_filename = f"{design_name}_study.csv"

    n_studies = len(next(iter(params.values())))
    with open(study_filename, "w", newline="") as study_file:
        writer = DictWriter(study_file, fieldnames=params.keys())
        writer.writeheader()
        for i in range(n_studies):
            writer.writerow({k: v[i] for k, v in params.items()})

    print(f"Study parameters written to {study_filename}.")
    return study_filename


def align_study_params(params):
    """Align the study parameters to the same number of runs.
    This allows to have single values and lists of parameter values.
    """

    n_studies = [len(v) for v in params.values() if isinstance(v, Sequence)]
    if n_studies:
        n_studies = max(n_studies)
    else:
        n_studies = 1

    aligned_params = {}
    for p_name in params:
        if isinstance(params[p_name], Sequence):
            if len(params[p_name]) != n_studies:
                raise ValueError(
                    f"Parameter {p_name} has {len(params[p_name])} values, "
                    f"but {n_studies} values are expected."
                )
            aligned_params[p_name] = params[p_name]
        else:
            aligned_params[p_name] = [params[p_name]] * n_studies

    return aligned_params


def sweep_study_param(params, param_name, values):
    """Add or modify a parameter to sweep it in the study parameters."""
    aligned_params = align_study_params(params)
    n_studies = len(next(iter(aligned_params.values())))
    swept_params = {}
    swept_params[param_name] = list(chain(*([v] * n_studies for v in values)))
    for p_name in aligned_params:
        if p_name != param_name:
            swept_params[p_name] = list(
                chain(aligned_params[p_name] * len(values))
            )
    return swept_params


def run_design(design_name, study_filename, config):
    minio = Minio(
        config.minio_url,
        access_key=config.minio_user,
        secret_key=config.minio_password,
        secure=False,
    )
    found = minio.bucket_exists(config.minio_bucket)
    if not found:
        print(f"Creating MinIO bucket {config.minio_bucket}")
        minio.make_bucket(config.minio_bucket)

    minio.fput_object(config.minio_bucket, study_filename, study_filename)
    print(f"Uploaded to MinIO {config.minio_bucket}/{study_filename}.")

    jenkins = Jenkins(
        config.jenkins_url,
        auth=(config.jenkins_user, config.jenkins_password),
    )
    if False:
        item = jenkins.build_job(
            "uam_direct2cad",
            graphGUID=design_name,
            minioBucket=config.minio_bucket,
            paramFile=study_filename,
        )
    else:
        job = jenkins.get_job("uam_direct2cad")
        # job.url is respose location, we need to override it
        job.url = config.jenkins_url + "job/uam_direct2cad/"
        item = job.build(
            graphGUID=design_name,
            minioBucket=config.minio_bucket,
            paramFile=study_filename,
        )
    if item:
        print("Queuing Jenkins job", end="")
        while not (build := item.get_build()):
            time.sleep(0.5)
            print(".", end="", flush=True)

        print(f"\nJenkins job started", build)


def run(args=None):
    import argparse
    from .platforms import designs  # avoid circular import

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "design",
        choices=designs.keys(),
        default=next(iter(designs)),
        nargs="?",
    )
    parser.add_argument(
        "-r", "--run", action="store_true", help="Run the design."
    )
    parser.add_argument(
        "--minio-url", default="localhost:9000", help="MinIO URL."
    )
    parser.add_argument(
        "--minio-user", default="symcps", help="MinIO username."
    )
    parser.add_argument(
        "--minio-password", default="symcps2021", help="MinIO password."
    )
    parser.add_argument(
        "--minio-bucket", default="symbench", help="MinIO bucket name."
    )
    parser.add_argument(
        "--jenkins-url",
        # default="http://localhost:8080/",
        default="http://laplace.isis.vanderbilt.edu:8080/",
        help="Jenkins URL.",
    )
    parser.add_argument(
        "--jenkins-user", default="symcps", help="Jenkins username."
    )
    parser.add_argument(
        "--jenkins-password", default="symcps2021", help="Jenkins password."
    )

    args = parser.parse_args(args)
    design_name, study_params = designs[args.design]()
    study_params = align_study_params(study_params)
    study_filename = write_study_params(design_name, study_params)

    if args.run:
        run_design(design_name, study_filename, args)


if __name__ == "__main__":
    run()
