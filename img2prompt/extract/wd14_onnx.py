"""WD14 (ConvNeXtV2) ONNX tagger with auto-download and robust I/O."""
from pathlib import Path
from typing import Dict
import logging

import numpy as np
import onnxruntime as ort
from PIL import Image
from huggingface_hub import hf_hub_download

logger = logging.getLogger(__name__)

MODEL_REPO = "SmilingWolf/wd-v1-4-convnextv2-tagger-v2"
MODEL_FILE = "wd14-convnextv2.onnx"
TAGS_FILE = "tags.csv"

_session = None
_tags = None


def _ensure_files(model_dir: Path) -> Path:
    """Ensure model and tag files exist, downloading if necessary."""
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / MODEL_FILE
    tags_path = model_dir / TAGS_FILE
    try:
        if not model_path.exists():
            hf_hub_download(MODEL_REPO, MODEL_FILE, local_dir=model_dir, local_dir_use_symlinks=False)
        if not tags_path.exists():
            hf_hub_download(MODEL_REPO, TAGS_FILE, local_dir=model_dir, local_dir_use_symlinks=False)
    except Exception as exc:  # pragma: no cover - network failures
        logger.warning("WD14 model download failed: %s", exc, exc_info=True)
    return model_path, tags_path


def _load() -> None:
    """Lazily load ONNX session and tags."""
    global _session, _tags
    if _session is not None and _tags is not None:
        return
    try:
        base = Path(__file__).resolve().parent / "models"
        model_path, tags_path = _ensure_files(base)
        if not model_path.exists() or not tags_path.exists():
            raise FileNotFoundError("WD14 model files missing")
        _session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
        _tags = [l.strip() for l in tags_path.read_text(encoding="utf-8").splitlines()]
    except Exception as exc:
        logger.warning("WD14 load failed: %s", exc, exc_info=True)
        _session, _tags = None, None


def extract_tags(path: Path, threshold: float = 0.35) -> Dict[str, float]:
    """Return tags for ``path`` using the WD14 ONNX model."""
    try:
        _load()
        if _session is None or _tags is None:
            raise RuntimeError("WD14 unavailable")

        img = Image.open(path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        if min(img.size) < 32:
            raise ValueError("image too small")
        img = img.resize((448, 448), Image.BICUBIC)
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
    except Exception as exc:  # pragma: no cover - inference failures
        logger.warning("WD14 inference failed: %s", exc, exc_info=True)
        return {}

