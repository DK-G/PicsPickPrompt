import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from img2prompt.assemble import bucketize


def test_bucketize_generates_unique_tags():
    tags = ["person", "hair", "outdoor", "close up", "soft lighting"]
    buckets = bucketize.bucketize(tags)
    all_tags = [t for v in buckets.values() for t in v]
    assert len(all_tags) == len(set(all_tags))
    total = len(all_tags)
    assert 50 <= total <= 70
