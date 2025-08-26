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
        while len(buckets[bucket]) < 5:
            filler = f"{bucket}_extra_{len(buckets[bucket]) + 1}"
            buckets[bucket].append(filler)
    total = sum(len(v) for v in buckets.values())
    extras_needed = max(0, 50 - total)
    for i in range(extras_needed):
        buckets["subject"].append(f"extra_tag_{i+1}")
    return buckets
