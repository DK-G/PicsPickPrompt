"""Image captioning using BLIP."""

from pathlib import Path
import logging
from typing import Optional


logger = logging.getLogger(__name__)

_processor = None
_model = None


def _load() -> None:
    """Load BLIP processor and model lazily."""
    global _processor, _model
    if _processor is not None and _model is not None:
        return
    try:
        from transformers import BlipProcessor, BlipForConditionalGeneration

        _processor = BlipProcessor.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        _model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        _model.eval()
    except Exception as exc:  # pragma: no cover - fallback path
        logger.exception("Failed to load BLIP model: %s", exc)
        _processor = None
        _model = None


def generate_caption(path: Path) -> str:
    """Generate an English caption for ``path``.

    Falls back to a generic caption on error.
    """

    try:
        _load()
        if _processor is None or _model is None:
            raise RuntimeError("BLIP model unavailable")

        from PIL import Image
        import torch

        image = Image.open(path).convert("RGB")
        inputs = _processor(images=image, return_tensors="pt")
        with torch.no_grad():
            out = _model.generate(**inputs, max_new_tokens=48)
        caption = _processor.decode(out[0], skip_special_tokens=True).strip()
        return caption or "an image"
    except Exception as exc:  # pragma: no cover - fallback path
        logger.exception("Caption generation failed: %s", exc)
        return "an image"
