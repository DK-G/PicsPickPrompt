import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from img2prompt.utils.text_filters import clean_tokens


def test_clean_tokens_drops_meta_and_counts():
    tokens = [
        "Artist Name",
        "soft lighting",
        "beautiful japanese girls face",
        "standing",
        "1girl",
        "1boy",
        "solo",
        "General",
        "valid token",
    ]
    out = clean_tokens(tokens)
    assert "soft lighting" in out
    assert "valid token" in out
    banned = {"artist name", "beautiful japanese girls face", "standing", "1girl", "1boy", "solo", "general"}
    assert not any(b in out for b in banned)
