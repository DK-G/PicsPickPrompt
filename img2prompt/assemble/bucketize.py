from itertools import cycle
from typing import Dict, List

# Seed tags for each bucket. These mirror the values that previously
# lived in ``presets/buckets.yaml`` but are inlined here so that the
# module has no external dependencies such as PyYAML.
BUCKET_SEEDS: Dict[str, List[str]] = {
    "subject": [
        "person",
        "portrait",
        "upper body",
        "full body",
        "hands",
        "looking at viewer",
        "face",
    ],
    "appearance": [
        "hair",
        "eyes",
        "smile",
        "blush",
        "uniform",
        "skirt",
        "ribbon",
        "bow",
        "shirt",
        "jacket",
        "accessory",
    ],
    "scene": [
        "indoor",
        "outdoor",
        "window",
        "street",
        "room",
        "forest",
        "sky",
        "night",
        "day",
    ],
    "composition": [
        "close up",
        "upper body",
        "full body",
        "profile",
        "from above",
        "from below",
        "symmetry",
        "rule of thirds",
    ],
    "style_lighting": [
        "soft lighting",
        "rim light",
        "volumetric light",
        "bokeh",
        "film grain",
        "35mm",
        "sharp focus",
        "depth of field",
        "natural light",
        "studio light",
    ],
}


def bucketize(tags: List[str]) -> Dict[str, List[str]]:
    """Split ``tags`` into semantic buckets ensuring unique entries.

    The function mirrors the original YAML-based configuration but operates on a
    Python dictionary so that it has no external dependencies. Each bucket is
    padded to at least five items and the combined prompt is filled up to
    50–70 total tags with non-duplicated seed values.
    """

    buckets: Dict[str, List[str]] = {k: [] for k in BUCKET_SEEDS}
    input_tags = set(tags)
    all_seeds = [s for seeds in BUCKET_SEEDS.values() for s in seeds]
    total_unique = len(set(all_seeds))
    used: set[str] = set()

    for bucket, seeds in BUCKET_SEEDS.items():
        for seed in seeds:
            if seed in input_tags and seed not in used:
                buckets[bucket].append(seed)
                used.add(seed)
        filler_cycle = cycle(seeds)
        while len(buckets[bucket]) < 5:
            filler = next(filler_cycle)
            if filler in buckets[bucket]:
                continue
            if filler in used and len(used) < total_unique:
                continue
            buckets[bucket].append(filler)
            used.add(filler)

    filler_cycle = cycle(all_seeds)
    total = sum(len(v) for v in buckets.values())
    while total < 50:
        candidate = next(filler_cycle)
        if candidate in buckets["subject"] and len(used) < total_unique:
            if candidate in used:
                continue
        if candidate in used and len(used) < total_unique:
            continue
        buckets["subject"].append(candidate)
        used.add(candidate)
        total += 1

    if total > 70:
        excess = total - 70
        buckets["subject"] = buckets["subject"][:-excess]

    return buckets
