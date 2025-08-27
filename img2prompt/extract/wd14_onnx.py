"""WD14 (ConvNeXtV2) ONNX tagger with auto-download and robust I/O."""
from pathlib import Path
from typing import Dict
import logging
import csv
import shutil

import numpy as np
import onnxruntime as ort
from PIL import Image
from huggingface_hub import hf_hub_download

logger = logging.getLogger(__name__)

MODEL_REPO = "SmilingWolf/wd-v1-4-convnextv2-tagger-v2"
MODEL_FILE = "model.onnx"
TAGS_FILE = "selected_tags.csv"

_session = None
_tags = None
_input_name = "input"


def _ensure_files(model_dir: Path):
    """Download model files to ``model_dir`` if missing."""
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / MODEL_FILE
    tags_path = model_dir / TAGS_FILE
    try:
        if not model_path.exists():
            tmp = hf_hub_download(MODEL_REPO, MODEL_FILE, local_dir=model_dir)
            shutil.move(tmp, model_path)
        if not tags_path.exists():
            tmp = hf_hub_download(MODEL_REPO, TAGS_FILE, local_dir=model_dir)
            shutil.move(tmp, tags_path)
    except Exception as exc:  # pragma: no cover - network failures
        logger.warning("WD14 model download failed: %s", exc, exc_info=True)
    return model_path, tags_path


def _load() -> None:
    """Lazily load ONNX session and tag list."""
    global _session, _tags, _input_name
    if _session is not None and _tags is not None:
        return
    try:
        bases = [
            Path(__file__).resolve().parent / "models",
            Path.cwd() / "models",
        ]
        model_path = tags_path = None
        for base in bases:
            mp, tp = base / MODEL_FILE, base / TAGS_FILE
            if mp.exists() and tp.exists():
                model_path, tags_path = mp, tp
                break
        if model_path is None or tags_path is None:
            model_path, tags_path = _ensure_files(bases[0])
        if not model_path.exists() or not tags_path.exists():
            raise FileNotFoundError("WD14 model files missing")
        _session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
        _input_name = _session.get_inputs()[0].name
        with tags_path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            _tags = [row[0] for row in reader if row and not row[0].startswith("rating:")]
    except Exception as exc:  # pragma: no cover - fallback path
        logger.warning("WD14 load failed: %s", exc, exc_info=True)
        _session, _tags = None, None


def extract_tags(path: Path, threshold: float = 0.35) -> Dict[str, float]:
    """Return tags for ``path`` using the WD14 ONNX model."""
    try:
        _load()
        if _session is None or _tags is None:
            raise RuntimeError("WD14 unavailable")

        img = Image.open(path).convert("RGB")
        img = img.resize((448, 448), Image.BICUBIC)
        x = np.asarray(img, dtype=np.float32) / 255.0
        x = x.transpose(2, 0, 1)[None, ...]
        y = _session.run(None, {_input_name: x})[0][0]
        out: Dict[str, float] = {}
        for tag, score in zip(_tags, y):
            s = float(score)
            if s >= threshold:
                out[tag.replace("_", " ")] = s
        return out
    except Exception as exc:  # pragma: no cover - inference failures
        logger.warning("WD14 inference failed: %s", exc, exc_info=True)
        return {}

