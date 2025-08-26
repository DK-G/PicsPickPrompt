import json
import sys
import copy
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from img2prompt.export import writer

EXAMPLE_PATH = ROOT / "examples" / "sample.prompt.json"


def test_example_conforms_to_schema():
    with open(EXAMPLE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    writer.validate_prompt(data)


def test_missing_required_key_raises():
    data = copy.deepcopy(writer.DEFAULT_DATA)
    data.pop("caption")
    with pytest.raises(ValueError):
        writer.validate_prompt(data)


def test_invalid_type_raises():
    data = copy.deepcopy(writer.DEFAULT_DATA)
    data["control_suggestions"]["ip_adapter_reference"] = "yes"
    with pytest.raises(ValueError):
        writer.validate_prompt(data)


def test_invalid_range_raises():
    data = copy.deepcopy(writer.DEFAULT_DATA)
    data["params"]["width"] = 0
    with pytest.raises(ValueError):
        writer.validate_prompt(data)
