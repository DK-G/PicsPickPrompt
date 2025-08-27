"""Extract style tags using CLIP Interrogator."""

from pathlib import Path
from typing import Dict, Tuple
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


def extract_tags(path: Path) -> Tuple[Dict[str, float], str]:
    """Run the interrogator and return tags and raw text."""
    try:
        from clip_interrogator import Config, Interrogator
        from PIL import Image

        cfg = Config()
        ci = Interrogator(cfg)
        image = Image.open(path).convert("RGB")
        text = ci.interrogate_fast(image).lower()

        result: Dict[str, float] = {}
        # 1) 既存の候補語ヒット（確度0.55）
        for cand in CANDIDATES:
            if cand in text:
                result[cand] = 0.55

        # 2) 追加フォールバック：テキストから句を抽出して拾う
        chunks = [c.strip() for c in re.split(r"[,\n]", text)]
        picked = []
        for c in chunks:
            if 2 <= len(c) <= 48 and any(k in c for k in KEYS):
                picked.append(c)
        for w in picked[:15]:
            result.setdefault(w, 0.50)

        return result, text
    except Exception as exc:  # pragma: no cover - fallback path
        logger.warning("CLIP Interrogator failed: %s", exc, exc_info=True)
        return {}, ""


def extract_text(path: Path) -> str:
    """Return raw interrogation text for ``path``."""
    try:
        from clip_interrogator import Config, Interrogator
        from PIL import Image

        cfg = Config()
        ci = Interrogator(cfg)
        image = Image.open(path).convert("RGB")
        return ci.interrogate_fast(image).lower()
    except Exception as exc:  # pragma: no cover - fallback path
        logger.warning("CLIP Interrogator text failed: %s", exc, exc_info=True)
        return ""
