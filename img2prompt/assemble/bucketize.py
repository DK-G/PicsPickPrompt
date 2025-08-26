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
    """Bucketize tags ensuring uniqueness and minimum counts.

    Tags are distributed into pre-defined buckets.  Each bucket receives up to
    one instance of each matching seed tag.  Any remaining slots are filled with
    deterministic ``*_extra_*`` filler values.  After seeding, additional filler
    tags are appended to the ``subject`` bucket so that the total number of tags
    falls within the 50--70 range.
    """

    buckets: Dict[str, List[str]] = {k: [] for k in BUCKET_SEEDS}
    used = set()
    for bucket, seeds in BUCKET_SEEDS.items():
        for seed in seeds:
            if seed in tags and seed not in used:
                buckets[bucket].append(seed)
                used.add(seed)
        while len(buckets[bucket]) < 5:
            filler = f"{bucket}_extra_{len(buckets[bucket]) + 1}"
            buckets[bucket].append(filler)
            used.add(filler)
    total = sum(len(v) for v in buckets.values())
    extras_needed = max(0, 50 - total)
    for i in range(extras_needed):
        filler = f"extra_tag_{i+1}"
        buckets["subject"].append(filler)
        used.add(filler)
    return buckets
