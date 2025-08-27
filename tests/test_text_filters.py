import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from img2prompt.utils.text_filters import clean_tokens


def test_clean_tokens_filters_noise_and_meta():
    tokens = [
        "Artist Name",
        "soft lighting",
        "beautiful japanese girls face",
        "twitter username",
        "1girl",
        "1boy",
        "solo",
        "General",
        "dated",
        "valid token",
    ]
    out = clean_tokens(tokens)
    assert "soft lighting" in out
    assert "valid token" in out
    banned = {
        "artist name",
        "beautiful japanese girls face",
        "twitter username",
        "1girl",
        "1boy",
        "solo",
        "general",
        "dated",
    }
    assert not any(b in out for b in banned)


def test_clean_tokens_strips_artist_names_case_insensitive():
    tokens = [
        "Ayami Kojima",
        "ayami kojima",
        "Makoto Shinkai",
        "soft lighting",
    ]
    out = clean_tokens(tokens)
    assert out == ["soft lighting"]


def test_clean_tokens_unifies_background_tags():
    tokens = [
        "white background",
        "grey background",
        "simple background",
        "clean background",
        "soft lighting",
    ]
    out = clean_tokens(tokens)
    backgrounds = [t for t in out if "background" in t]
    assert backgrounds == ["white background"]
    assert "soft lighting" in out

