import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from img2prompt.assemble import style_picker


def test_pick_style_anime():
    tags = ["anime", "blue hair"]
    assert style_picker.pick_style(tags) == "anime"


def test_pick_style_photo():
    tags = ["portrait", "outdoor"]
    assert style_picker.pick_style(tags) == "photo"
