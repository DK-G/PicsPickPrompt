"""Tag extraction using the official DeepDanbooru project."""

from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)

_model = None
_tags = None


def _load() -> None:
    """Lazily load the DeepDanbooru model."""
    global _model, _tags
    if _model is not None and _tags is not None:
        return
    import deepdanbooru as dd  # type: ignore

    project_path = dd.project.default_project_path()
    _model = dd.project.load_model_from_project(project_path)
    _tags = dd.project.load_tags_from_project(project_path)
    _model.eval()


def extract_tags(path: Path, threshold: float = 0.35) -> Dict[str, float]:
    """Return tags and scores for ``path``."""

    _load()
    if _model is None or _tags is None:
        raise RuntimeError("DeepDanbooru model unavailable")

    try:
        from PIL import Image
        import numpy as np
        import torch

        image = Image.open(path).convert("RGB")
        image = image.resize((512, 512))
        x = np.asarray(image, dtype=np.float32) / 255.0
        x = x[None, ...]
        with torch.no_grad():
            y = _model(x)[0].numpy()

        result: Dict[str, float] = {}
        for tag, score in zip(_tags, y):
            if score >= threshold and not tag.startswith("rating:"):
                tag = tag.replace("_", " ")
                result[tag] = float(score)
        return result
    except Exception as exc:  # pragma: no cover - inference failures
        raise RuntimeError(str(exc)) from exc
