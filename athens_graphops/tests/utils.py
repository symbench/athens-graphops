import json
from pathlib import Path


def get_design_dict(name):
    root_path = Path(__file__).resolve().parent.parent.parent / "designs"
    design_json_file = root_path / f"{name}.json"

    if not design_json_file.exists():
        raise FileNotFoundError(f"No design by the name {name} found in the designs directory")

    with open(design_json_file, "rb") as json_file:
        return json.load(json_file)[0]
