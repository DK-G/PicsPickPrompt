import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from img2prompt.extract import wd14_onnx


def test_postprocess_filters_numeric_and_character(monkeypatch):
    # Setup dummy names and categories
    names = ["123", "some_character", "valid_tag"]
    cats = ["general", "character", "general"]
    scores = np.array([0.9, 0.8, 0.95])
    monkeypatch.setattr(wd14_onnx, "_names", names)
    monkeypatch.setattr(wd14_onnx, "_cats", cats)
    result = wd14_onnx._postprocess_wd14(scores, threshold=0.25)
    assert result == {"valid tag": 0.95}
