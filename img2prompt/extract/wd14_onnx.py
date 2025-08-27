"""WD14 (ConvNeXtV2) ONNX tagger with auto-download and robust I/O."""
from pathlib import Path
from typing import Dict, List, Tuple
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
_tags: List[Tuple[str, str]] | None = None


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
    global _session, _tags
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
        names: List[str] = []
        cats: List[str] = []
        with tags_path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if not row:
                    continue
                names.append(row[0])
                cats.append(row[1] if len(row) > 1 else "general")
        _tags = list(zip(names, cats))
    except Exception as exc:  # pragma: no cover - fallback path
        logger.warning("WD14 load failed: %s", exc, exc_info=True)
        _session, _tags = None, None


def extract_tags(path: Path, threshold: float = 0.25) -> Dict[str, float]:
    """Return tags for ``path`` using the WD14 ONNX model."""
    try:
        _load()
        if _session is None or _tags is None:
            raise RuntimeError("WD14 unavailable")

        img = Image.open(path).convert("RGB").resize((448, 448), Image.BICUBIC)
        x = np.asarray(img, dtype=np.float32) / 255.0  # (448,448,3)
        x = x[np.newaxis, ...]  # (1,448,448,3)
        input_name = _session.get_inputs()[0].name
        y = _session.run(None, {input_name: x})[0][0]  # (num_tags,)
        out: Dict[str, float] = {}
        assert _tags is not None  # for type checkers
        for (tag, cat), score in zip(_tags, y.tolist()):
            s = float(score)
            if (
                s >= threshold
                and not tag.startswith("rating:")
                and cat != "character"
            ):
                out[tag.replace("_", " ")] = s
        return out
    except Exception as exc:  # pragma: no cover - inference failures
        logger.warning("WD14 inference failed: %s", exc, exc_info=True)
        return {}

