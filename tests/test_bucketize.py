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
