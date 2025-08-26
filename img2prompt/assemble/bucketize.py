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
    buckets: Dict[str, List[str]] = {k: [] for k in BUCKET_SEEDS}
    remaining = list(tags)
    for bucket, seeds in BUCKET_SEEDS.items():
        for seed in seeds:
            if seed in remaining and seed not in buckets[bucket]:
                buckets[bucket].append(seed)
        filler_cycle = cycle(seeds)
        while len(buckets[bucket]) < 5:
            filler = next(filler_cycle)
            if filler not in buckets[bucket]:
                buckets[bucket].append(filler)

    total = sum(len(v) for v in buckets.values())
    if total < 50:
        all_seeds = [s for seeds in BUCKET_SEEDS.values() for s in seeds]
        filler_cycle = cycle(all_seeds)
        while total < 50:
            buckets["subject"].append(next(filler_cycle))
            total += 1
    if total > 70:
        excess = total - 70
        buckets["subject"] = buckets["subject"][:-excess]
    return buckets
