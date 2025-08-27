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
    ci_low = (ci_raw or "").lower()
    anime_hits = sum(
        k in ci_low for k in ["anime", "manga", "comic", "cartoon", "cel shading"]
    )
    photo_hits = sum(
        k in ci_low
        for k in [
            "35mm",
            "film grain",
            "bokeh",
            "studio light",
            "natural light",
            "cinematic",
            "photograph",
            "dslr",
            "lens",
        ]
    )

    if anime_hits >= 2 and photo_hits == 0:
        style = "anime"
    else:
        style = "photo"

    params = PHOTO_PARAMS if style == "photo" else ANIME_PARAMS
    return style, params
