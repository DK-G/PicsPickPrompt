"""Tag normalization and merging utilities."""

from collections import defaultdict
from typing import Dict

SYNONYMS = {
    "serafuku": "school uniform",
}

# Prefixes used by earlier prototypes for placeholder tags. These should never
# appear in final prompts, so we filter them out before further processing.
PLACEHOLDER_PREFIXES = ("subject_extra_", "extra_tag_")


def remove_placeholders(tags: Dict[str, float]) -> Dict[str, float]:
    """Remove any placeholder tags from ``tags``.

    Placeholders such as ``subject_extra_1`` or ``extra_tag_2`` were used in
    earlier versions to pad prompts. They must be excluded to produce clean
    outputs compliant with the acceptance criteria.
    """

    return {
        tag: score
        for tag, score in tags.items()
        if not any(tag.startswith(pref) for pref in PLACEHOLDER_PREFIXES)
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
