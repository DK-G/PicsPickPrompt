"""Determine style and recommended generation parameters."""

from typing import Dict, Tuple


def determine_style(ci_raw: str, wd14_tags: Dict[str, float]) -> Tuple[str, Dict[str, float]]:
    ci_low = (ci_raw or "").lower()
    anime_hits = sum(k in ci_low for k in ["anime","manga","comic","cartoon","cel shading"])

    photo_hits = sum(k in ci_low for k in [
        "35mm","film grain","bokeh","studio light","natural light","cinematic","photograph","dslr","lens"
    ])

    if photo_hits >= 1 and anime_hits == 0:
        style = "photo"
    elif anime_hits >= 2:
        style = "anime"
    else:
        # WD14補助：アニメ強語が多いか
        wd14_join = " ".join(wd14_tags.keys())
        anime2 = sum(k in wd14_join for k in ["anime","manga","comic","cartoon"]) >= 2
        style = "anime" if anime2 else "photo"

    params = (
      {"width":896,"height":1152,"steps":30,"cfg_scale":6.0,"sampler":"DPM++ 2M Karras","seed":"random"}
      if style=="photo" else
      {"width":768,"height":1024,"steps":28,"cfg_scale":6.5,"sampler":"Euler a","seed":"random"}
    )
    return style, params
