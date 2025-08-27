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
        k in ci_low for k in ["anime", "manga", "comic", "cartoon", "cel shading", "illustration"]
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

    if anime_hits > photo_hits:
        style = "anime"
    elif photo_hits > anime_hits:
        style = "photo"
    else:
        # WD14補助：アニメ強語が多いか
        wd14_join = " ".join(wd14_tags.keys())
        anime_present = any(
            k in wd14_join for k in ["anime", "manga", "comic", "cartoon", "illustration"]
        )
        style = "anime" if anime_present else "photo"

    params = PHOTO_PARAMS if style == "photo" else ANIME_PARAMS
    return style, params
