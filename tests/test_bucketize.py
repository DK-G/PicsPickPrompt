import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from img2prompt.assemble import bucketize


def test_bucketize_generates_minimum_tags():
    tags = ["person", "hair", "outdoor", "close up", "soft lighting"]
    buckets = bucketize.bucketize(tags)
    assert all(len(v) >= 5 for v in buckets.values())
    total = sum(len(v) for v in buckets.values())
    assert 50 <= total <= 70
