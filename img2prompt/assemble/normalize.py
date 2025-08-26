"""Tag normalization and merging utilities."""

from collections import defaultdict
from typing import Dict

SYNONYMS = {
    "serafuku": "school uniform",
}


def merge_tags(dd: Dict[str, float], ci: Dict[str, float]) -> Dict[str, float]:
    """Merge DeepDanbooru and CLIP Interrogator tags with weighting."""

    combined: Dict[str, float] = defaultdict(float)
    for tag, score in dd.items():
        combined[tag] += score * 1.0
    for tag, score in ci.items():
        combined[tag] += score * 0.9

    normalized: Dict[str, float] = {}
    for tag, score in combined.items():
        canonical = SYNONYMS.get(tag, tag)
        if canonical in normalized:
            normalized[canonical] = max(normalized[canonical], score)
        else:
            normalized[canonical] = score
    # Return tags sorted by score descending for deterministic ordering
    return dict(sorted(normalized.items(), key=lambda x: x[1], reverse=True))
