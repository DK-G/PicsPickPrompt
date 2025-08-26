from typing import Iterable, List

SYNONYMS = {
    "serafuku": "school uniform",
}


def normalize_tags(tags: Iterable[str]) -> List[str]:
    seen = set()
    normalized: List[str] = []
    for tag in tags:
        tag = SYNONYMS.get(tag, tag)
        if tag not in seen:
            normalized.append(tag)
            seen.add(tag)
    return normalized
