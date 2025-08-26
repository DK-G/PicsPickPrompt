from typing import Dict, List

# Seed tags for each bucket used for initial categorisation.
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


BUCKET_ORDER = list(BUCKET_SEEDS.keys())


def bucketize(tags: Dict[str, float]) -> Dict[str, List[str]]:
    """Distribute tags into semantic buckets.

    Each bucket is limited to ten tags. Remaining tags are appended to an
    "extra" bucket until the overall total reaches at most seventy tags.
    Duplicates are removed.
    """

    buckets: Dict[str, List[str]] = {k: [] for k in BUCKET_ORDER}
    buckets["extra"] = []
    used = set()

    sorted_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)

    # First pass – assign tags matching seeds
    for bucket, seeds in BUCKET_SEEDS.items():
        for tag, _ in sorted_tags:
            if tag in seeds and tag not in used and len(buckets[bucket]) < 10:
                buckets[bucket].append(tag)
                used.add(tag)

    # Collect remaining tags
    remaining = [(t, s) for t, s in sorted_tags if t not in used]

    # Round-robin fill up to 10 per bucket
    idx = 0
    while remaining and any(len(buckets[b]) < 10 for b in BUCKET_ORDER):
        bucket = BUCKET_ORDER[idx % len(BUCKET_ORDER)]
        if len(buckets[bucket]) < 10:
            tag, _ = remaining.pop(0)
            if tag not in used:
                buckets[bucket].append(tag)
                used.add(tag)
        idx += 1

    # Add any leftover tags to the extra bucket up to a total of 70
    total = sum(len(v) for v in buckets.values())
    while remaining and total < 70:
        tag, _ = remaining.pop(0)
        if tag not in used:
            buckets["extra"].append(tag)
            used.add(tag)
            total += 1

    return buckets
