import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from img2prompt.export import writer

EXAMPLE_PATH = ROOT / "examples" / "sample.prompt.json"


def load_example() -> dict:
    with open(EXAMPLE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_example_conforms_to_schema():
    data = load_example()
    writer.validate_prompt(data)


def test_missing_required_key_raises():
    data = load_example()
    del data["prompt"]
    with pytest.raises(ValueError):
        writer.validate_prompt(data)


def test_invalid_type_raises():
    data = load_example()
    data["caption"] = 123
    with pytest.raises(ValueError):
        writer.validate_prompt(data)


def test_invalid_range_raises():
    data = load_example()
    data["params"]["width"] = -1
    with pytest.raises(ValueError):
        writer.validate_prompt(data)
