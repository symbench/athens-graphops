import os

import pytest
from deepdiff import DeepDiff

from athens_graphops import CONFIG
from athens_graphops.json_designer import JSONUAVDesign
from athens_graphops.query import Client
from athens_graphops.tests.utils import get_design_dict

TEST_DESIGNS = [
    "FalconM4",
    "FalconT8",
    "FalconM4b",
    "FalconS4",
]

SINGLE_RUN_TIMEOUT = 500


class TestDesign:
    @pytest.mark.parametrize("design_name", TEST_DESIGNS)
    def test_deep_equality(self, design_name):
        old_dict = get_design_dict(design_name)
        design = JSONUAVDesign.from_dict(old_dict)
        new_dict = design.to_dict()
        diff = DeepDiff(old_dict, new_dict)
        assert diff == {}

    @pytest.mark.skipif(
        condition=os.environ.get("GRAPH_DB_ADDR") is None,
        reason="Cannot communicate with graphdb",
    )
    @pytest.mark.timeout(SINGLE_RUN_TIMEOUT)
    @pytest.mark.parametrize("design_name", TEST_DESIGNS)
    def test_deep_equality_with_graphdb(self, design_name):
        CONFIG["hostname"] = os.environ.get("GRAPH_DB_ADDR")
        old_dict = get_design_dict(design_name)
        design = JSONUAVDesign.from_dict(old_dict)
        design.instantiate(new_name=design_name + "_2", overwrite=True)
        client = Client()
        new_dict = client.get_design_data(design_name + "_2")[0]
        client.delete_design(design_name + "_2")
        client.close()
        assert DeepDiff(old_dict, new_dict, exclude_paths="design") == {}
