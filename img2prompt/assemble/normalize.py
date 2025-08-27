"""Tag normalization and merging utilities."""

from collections import defaultdict
from typing import Dict, List

from ..utils.text_filters import strip_names

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


def merge_tags(
    wd: Dict[str, float], dd: Dict[str, float], ci: Dict[str, float]
) -> Dict[str, float]:
    """Merge tag sources with weighting."""

    combined: Dict[str, float] = defaultdict(float)

    def add(src: Dict[str, float], weight: float) -> None:
        for tag, score in src.items():
            combined[tag] = max(combined.get(tag, 0.0), score * weight)

    add(wd, 1.0)
    add(dd, 0.8)
    add(ci, 0.7)

    normalized: Dict[str, float] = {}
    for tag, score in combined.items():
        canonical = SYNONYMS.get(tag, tag)
        if canonical in normalized:
            normalized[canonical] = max(normalized[canonical], score)
        else:
            normalized[canonical] = score
    return dict(sorted(normalized.items(), key=lambda x: x[1], reverse=True))


def strip_name_tokens(tags: List[str]) -> List[str]:
    """Remove personal names or banned tokens from ``tags``.

    This uses simple heuristics to filter out two-word western style
    names and known bad tokens that should not appear in prompts.
    """

    return strip_names(tags)
