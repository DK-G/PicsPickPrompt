import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from img2prompt.assemble import bucketize


def test_bucketize_word_count_and_no_duplicates():
    tags = {f"tag{i}": 1.0 for i in range(80)}
    tags.update({
        "person": 1.0,
        "hair": 1.0,
        "outdoor": 1.0,
        "close up": 1.0,
        "soft lighting": 1.0,
    })
    buckets = bucketize.bucketize(tags)
    total = sum(len(v) for v in buckets.values())
    assert 50 <= total <= 70
    all_tags = [t for bucket in buckets.values() for t in bucket]
    assert len(all_tags) == len(set(all_tags))


def test_ensure_50_70_respects_allow_and_background():
    from img2prompt.utils.text_filters import is_bad_token

    tags = ["soft lighting", "1girl", "white background", "black background"]
    out = bucketize.ensure_50_70(
        tags,
        caption="",
        ci_picks=[],
        min_total=0,
        max_total=10,
        allow=lambda w: not is_bad_token(w),
    )
    assert "1girl" not in out
    backgrounds = [t for t in out if "background" in t]
    assert backgrounds == ["white background"]


def test_is_bad_token_meta_exact_and_finalize():
    from img2prompt.utils.text_filters import (
        is_bad_token,
        finalize_prompt_safe,
        SAFE_FILL,
    )

    for w in ["text focus", "no humans", "multiple girls"]:
        assert is_bad_token(w)

    # ensure finalize fills with safe tokens only
    base = ["portrait"]
    out = finalize_prompt_safe(base.copy(), min_total=5, max_total=10)
    assert len(out) >= 5
    assert all(t in SAFE_FILL or t == "portrait" for t in out)
