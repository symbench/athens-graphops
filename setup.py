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

from setuptools import setup

setup(
    name='athens-graphops',
    version='0.1',
    packages=['athens_graphops'],
    license='GPL 3',
    description="Sciprts to access the Athens graph database",
    long_description=open('README.md').read(),
    python_requires='>3.6',
    # do not list standard packages
    install_requires=[
        "gremlinpython<=3.5",
        "api4jenkins",
        "creopyson",
        "pyyaml",
        "pydantic",
        "minio",
        "gql[all]",
        "python-dotenv",
    ],
    entry_points={
        'console_scripts': [
            'athens-graphops = athens_graphops.__main__:run'
        ]
    }
)
