"""Extract style tags using CLIP Interrogator."""

from pathlib import Path
from typing import Dict, List, Tuple
import logging
import re

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

KEYS = [
    "lighting",
    "light",
    "bokeh",
    "grain",
    "35mm",
    "cinematic",
    "sharp focus",
    "depth of field",
    "studio",
    "natural",
    "photograph",
]


def extract_tags(path: Path) -> Tuple[Dict[str, float], List[str], str]:
    """Return (tags_with_scores, picked_phrases, raw_text)."""
    try:
        from clip_interrogator import Config, Interrogator
        from PIL import Image

        ci = Interrogator(Config())
        text = ci.interrogate_fast(Image.open(path).convert("RGB")).lower()

        result: Dict[str, float] = {}

        # Existing fixed candidates scored at 0.55
        for cand in CANDIDATES:
            if cand in text:
                result[cand] = 0.55

        # Extract phrases from raw text that contain key words
        chunks = [c.strip() for c in re.split(r"[,\n]", text)]
        picks: List[str] = []
        for c in chunks:
            if 2 <= len(c) <= 48 and any(k in c for k in KEYS):
                if c not in picks:
                    picks.append(c)
        for w in picks[:15]:
            result.setdefault(w, 0.50)

        return result, picks[:15], text
    except Exception as exc:  # pragma: no cover - fallback path
        logger.warning("CLIP Interrogator failed: %s", exc, exc_info=True)
        return {}, [], ""
