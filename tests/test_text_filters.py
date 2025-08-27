import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from img2prompt.utils.text_filters import (
    clean_tokens,
    dedupe_background,
    drop_contradictions,
    finalize_pipeline,
    is_bad_token,
)


def test_clean_tokens_filters_noise_and_meta():
    tokens = [
        "Artist Name",
        "soft lighting",
        "beautiful japanese girls face",
        "twitter username",
        "1girl",
        "1boy",
        "solo",
        "standing",
        "General",
        "dated",
        "negative space",
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
        "standing",
        "general",
        "dated",
        "negative space",
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


def test_clean_tokens_filters_artist_name_typos():
    tokens = [
        "ayami koj ima",
        "matoko shinkai",
        "deayami kojima",
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


def test_clean_tokens_strips_single_name_tokens():
    tokens = ["ayami", "shinkai", "soft lighting"]
    out = clean_tokens(tokens)
    assert out == ["soft lighting"]


def test_dedupe_background_removes_extra_backgrounds():
    tags = ["white background", "clean background", "soft lighting"]
    out = dedupe_background(tags)
    assert out == ["white background", "soft lighting"]


def test_is_bad_token_handles_whitelist_and_bans():
    assert is_bad_token("1girl")
    assert is_bad_token("Makoto Shinkai")
    assert is_bad_token("123")
    assert not is_bad_token("soft lighting")


def test_drop_contradictions_removes_conflicting_tags():
    tags = [
        "long hair",
        "short hair",
        "smile",
        "closed mouth",
        "looking at camera",
        "closed eyes",
        "soft lighting",
    ]
    out = drop_contradictions(tags)
    assert "long hair" not in out
    assert "short hair" not in out
    assert "closed mouth" not in out
    assert "closed eyes" not in out
    assert "smile" in out
    assert "looking at camera" in out
    assert "soft lighting" in out


def test_finalize_pipeline_fills_and_filters():
    sample = [
        "portrait",
        "long hair",
        "short hair",
        "clean background",
        "ayami koj ima",
        "looking at camera",
    ]
    cleaned = clean_tokens(sample)
    out = finalize_pipeline(cleaned)
    assert 55 <= len(out) <= 65
    assert "ayami koj ima" not in out
    assert not ({"long hair", "short hair"} & set(out))

