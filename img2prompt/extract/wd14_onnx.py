"""WD14 (ConvNeXtV2) ONNX tagger."""
from pathlib import Path
from typing import Dict
import logging
import onnxruntime as ort
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

_session = None
_tags = None


def _load():
    global _session, _tags
    if _session is not None and _tags is not None:
        return
    try:
        model_path = Path("models/wd14-convnextv2.onnx")
        tags_path = Path("models/tags.csv")
        _session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
        _tags = [l.strip() for l in tags_path.read_text(encoding="utf-8").splitlines()]
    except Exception as exc:
        logger.warning("WD14 load failed: %s", exc, exc_info=True)
        _session, _tags = None, None


def extract_tags(path: Path, threshold: float = 0.35) -> Dict[str, float]:
    try:
        _load()
        if _session is None or _tags is None:
            raise RuntimeError("WD14 unavailable")
        img = Image.open(path).convert("RGB").resize((448, 448), Image.BICUBIC)
        x = np.asarray(img, dtype=np.float32) / 255.0
        x = x.transpose(2, 0, 1)[None, ...]
        y = _session.run(None, {"input": x})[0][0]
        out: Dict[str, float] = {}
        for tag, score in zip(_tags, y):
            s = float(score)
            if s >= threshold:
                t = tag.replace("_", " ")
                out[t] = s
        return out
    except Exception as exc:
        logger.warning("WD14 inference failed: %s", exc, exc_info=True)
        return {}

