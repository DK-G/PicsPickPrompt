"""WD14 (ConvNeXtV2) ONNX tagger with auto-download and robust I/O."""
from pathlib import Path
from typing import Dict, List
import logging
import csv
import shutil
import re

import numpy as np
from PIL import Image
from huggingface_hub import hf_hub_download

try:  # pragma: no cover - optional dependency for tests
    import onnxruntime as ort
except Exception:  # pragma: no cover - handled gracefully at runtime
    ort = None  # type: ignore

logger = logging.getLogger(__name__)

MODEL_REPO = "SmilingWolf/wd-v1-4-convnextv2-tagger-v2"
MODEL_FILE = "model.onnx"
TAGS_FILE = "selected_tags.csv"

NUMERIC_PAT = re.compile(r"^\d+$")

_session = None
_names: List[str] | None = None
_cats: List[str] | None = None


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


def _read_wd14_tags_csv(tags_path: Path) -> tuple[List[str], List[str]]:
    names: List[str] = []
    cats: List[str] = []
    with open(tags_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            n = row.get("name", "").strip()
            c = row.get("category", "general").strip().lower()
            if not n:
                continue
            names.append(n)
            cats.append(c)
    return names, cats


def _load() -> None:
    """Lazily load ONNX session and tag list."""
    global _session, _names, _cats
    if _session is not None and _names is not None and _cats is not None:
        return
    try:
        if ort is None:
            raise RuntimeError("onnxruntime not installed")

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
        _names, _cats = _read_wd14_tags_csv(tags_path)
    except Exception as exc:  # pragma: no cover - fallback path
        logger.warning("WD14 load failed: %s", exc, exc_info=True)
        _session, _names, _cats = None, None, None


def _postprocess_wd14(scores, threshold: float = 0.25) -> Dict[str, float]:
    assert _names is not None and _cats is not None
    out: Dict[str, float] = {}
    for tag, cat, score in zip(_names, _cats, scores.tolist()):
        s = float(score)
        if s < threshold:
            continue
        if tag.startswith("rating:"):
            continue
        if cat == "character":
            continue
        tag_norm = tag.replace("_", " ").strip().lower()
        if NUMERIC_PAT.match(tag_norm):
            continue
        out[tag_norm] = s
    return dict(sorted(out.items(), key=lambda kv: kv[1], reverse=True)[:50])


def extract_tags(path: Path, threshold: float = 0.25) -> Dict[str, float]:
    """Return tags for ``path`` using the WD14 ONNX model."""
    try:
        _load()
        if _session is None or _names is None or _cats is None:
            raise RuntimeError("WD14 unavailable")

        img = Image.open(path).convert("RGB").resize((448, 448), Image.BICUBIC)
        x = np.asarray(img, dtype=np.float32) / 255.0  # (448,448,3)
        x = x[np.newaxis, ...]  # (1,448,448,3)
        input_name = _session.get_inputs()[0].name
        y = _session.run(None, {input_name: x})[0][0]  # (num_tags,)
        return _postprocess_wd14(y, threshold)
    except Exception as exc:  # pragma: no cover - inference failures
        logger.warning("WD14 inference failed: %s", exc, exc_info=True)
        return {}

