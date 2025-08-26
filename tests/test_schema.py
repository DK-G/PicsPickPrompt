import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from img2prompt.export import writer

EXAMPLE_PATH = ROOT / "examples" / "sample.prompt.json"


def test_example_conforms_to_schema():
    with open(EXAMPLE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    writer.validate_prompt(data)
