import pytest

from deepdiff import DeepDiff
from athens_graphops.json_designer import JSONUAVDesign
from athens_graphops.tests.utils import get_design_dict


class TestDesign:
    @pytest.mark.parametrize("design_name", ["NewAxe_Seed", "TestQuad_seed"])
    def test_deep_equality(self, design_name):
        old_dict = get_design_dict(design_name)
        design = JSONUAVDesign.from_dict(old_dict)
        new_dict = design.to_dict()
        diff = DeepDiff(old_dict, new_dict)
        assert diff == {}

