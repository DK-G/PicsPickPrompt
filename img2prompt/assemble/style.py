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


def determine_style(ci_text: str) -> Tuple[str, Dict[str, float]]:
    """Classify style as 'anime' or 'photo' from CLIP Interrogator text."""

    cues = ["35mm", "film grain", "bokeh", "studio light", "natural light", "cinematic"]
    text = ci_text.lower()
    if any(c in text for c in cues):
        return "photo", PHOTO_PARAMS.copy()
    return "anime", ANIME_PARAMS.copy()
