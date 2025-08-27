"""Extract style tags using CLIP Interrogator."""

from pathlib import Path
from typing import Dict, List, Tuple
import logging
import re

logger = logging.getLogger(__name__)


def extract_tags(path: Path) -> Tuple[Dict[str, float], List[str], str]:
    """Return (tags_with_scores, picked_phrases, raw_text)."""
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
    try:
        from clip_interrogator import Config, Interrogator
        from PIL import Image

        ci = Interrogator(Config())
        raw = ci.interrogate_fast(Image.open(path).convert("RGB")).lower()

        result: Dict[str, float] = {}

        picks: List[str] = []
        seen = set()
        for chunk in re.split(r"[,\n]", raw):
            w = chunk.strip()
            if 2 <= len(w) <= 48 and any(k in w for k in KEYS):
                if w not in seen:
                    seen.add(w)
                    picks.append(w)
        for w in picks[:15]:
            result.setdefault(w, 0.50)

        return result, picks[:15], raw
    except Exception as exc:  # pragma: no cover - fallback path
        logger.warning("CLIP Interrogator failed: %s", exc, exc_info=True)
        return {}, [], ""
