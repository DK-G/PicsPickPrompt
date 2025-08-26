"""Extract style tags using CLIP Interrogator."""

from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)

CANDIDATES = [
    "soft lighting",
    "volumetric light",
    "rim light",
    "film grain",
    "bokeh",
    "35mm",
    "sharp focus",
    "depth of field",
    "natural light",
    "studio light",
]


def extract_tags(path: Path) -> Dict[str, float]:
    """Run the interrogator and return detected lighting/style tags."""
    try:
        from clip_interrogator import Config, Interrogator
        from PIL import Image

        cfg = Config()
        ci = Interrogator(cfg)
        image = Image.open(path).convert("RGB")
        text = ci.interrogate_fast(image).lower()
        result: Dict[str, float] = {}
        for cand in CANDIDATES:
            if cand in text:
                result[cand] = 0.55
        return result
    except Exception as exc:  # pragma: no cover - fallback path
        logger.exception("CLIP Interrogator failed: %s", exc)
        return {}
