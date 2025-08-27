from typing import Dict, List
import re


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


FLOOR = [
  "portrait","upper body","looking at camera","soft lighting","warm tones",
  "sharp focus","depth of field","wooden interior","window light","cozy atmosphere",
  "warm highlights","gentle shadow","natural skin tones","ambient light"
]
FILLER_BANK = [
  "balanced composition","eye level view","soft contrast","realistic texture",
  "warm color palette","fine details","cinematic feel","subtle bokeh",
  "clean background","subtle shadows","smooth gradients","natural highlights",
  "muted colors","shallow depth","soft focus"
]

def ensure_50_70(
    tags: List[str],
    caption: str,
    ci_picks: List[str],
    min_total: int = 55,
    max_total: int = 70,
    allow=None,
) -> List[str]:
    allow = allow or (lambda w: True)
    nounish = [
        p.strip()
        for p in re.findall(r"[a-z][a-z ]{2,40}", (caption or "").lower())
        if 1 <= len(p.split()) <= 4
    ]

    merged: List[str] = []
    seen: set[str] = set()

    def add_many(src: List[str] | None, limit: int | None = None) -> None:
        nonlocal merged
        for w in src or []:
            w = (w or "").strip(" ,").lower()
            if not w or w in seen:
                continue
            if not allow(w):
                continue
            if 2 <= len(w) <= 40:
                merged.append(w)
                seen.add(w)
                if limit and len(merged) >= limit:
                    break

    add_many(tags)
    if len(merged) < min_total:
        add_many(nounish, limit=min_total)
    if len(merged) < min_total:
        add_many(ci_picks, limit=min_total)
    if len(merged) < min_total:
        add_many(FLOOR, limit=min_total)
    if len(merged) < min_total:
        add_many(FILLER_BANK, limit=min_total)
    return merged[:max_total]
