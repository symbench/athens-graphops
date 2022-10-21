import pytest

from deepdiff import DeepDiff
from athens_graphops.design import Design
from athens_graphops.tests.utils import get_design_dict

class TestDesign:
    @pytest.mark.parametrize("design_name", ["Minimal", "NewAxe_Cargo", "NewAxe_seed"])
    def test_deep_equality(self, design_name):
        old_dict = get_design_dict(design_name)
        design = Design.from_dict(old_dict)
        new_dict = design.to_dict()
        diff = DeepDiff(old_dict, new_dict)
        print(diff)
        assert diff == {}
