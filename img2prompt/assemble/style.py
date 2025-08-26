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


def determine_style(dd_tags: Dict[str, float], ci_tags: Dict[str, float]) -> Tuple[str, Dict[str, float]]:
    """Classify style as 'anime' or 'photo' and return suggested params."""

    # Simple heuristic: presence of photographic cues or low DD tag count
    if "35mm" in ci_tags or "film grain" in ci_tags or len(dd_tags) < 30:
        return "photo", PHOTO_PARAMS.copy()
    return "anime", ANIME_PARAMS.copy()
