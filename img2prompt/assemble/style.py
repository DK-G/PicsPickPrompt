"""Determine style and recommended generation parameters."""

from typing import Dict, Tuple

PHOTO_PARAMS = {
    "width": 896,
    "height": 1152,
    "steps": 30,
    "cfg_scale": 6.0,
    "sampler": "DPM++ 2M Karras",
    "seed": "random",
}

ANIME_PARAMS = {
    "width": 768,
    "height": 1024,
    "steps": 28,
    "cfg_scale": 6.5,
    "sampler": "Euler a",
    "seed": "random",
}


def determine_style(ci_raw: str, wd14_tags: Dict[str, float]) -> Tuple[str, Dict[str, float]]:
    """Classify style as 'anime' or 'photo'.

    Preference is given to photographic style when the CLIP Interrogator text
    contains photo cues. If those cues are absent, WD14 tags are inspected and
    the absence of anime/comic indicators also results in a photo style.
    """

    cues = [
        "35mm",
        "film grain",
        "bokeh",
        "studio light",
        "natural light",
        "cinematic",
        "photograph",
    ]
    ci_low = (ci_raw or "").lower()
    photo = any(c in ci_low for c in cues)

    if not photo:
        wd14_join = " ".join(wd14_tags.keys())
        photo = not any(k in wd14_join for k in ["anime", "manga", "comic", "cartoon"])

    style = "photo" if photo else "anime"
    params = PHOTO_PARAMS.copy() if style == "photo" else ANIME_PARAMS.copy()
    return style, params
