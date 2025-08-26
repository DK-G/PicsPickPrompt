"""Prompt JSON writer with basic schema validation."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

REQUIRED_TOP_LEVEL = {
    "caption",
    "prompt",
    "negative_prompt",
    "style",
    "model_suggestion",
    "params",
    "control_suggestions",
    "meta",
}

REQUIRED_PARAMS = {
    "width",
    "height",
    "steps",
    "cfg_scale",
    "sampler",
    "seed",
}

REQUIRED_CONTROLS = {"ip_adapter_reference", "openpose"}
REQUIRED_META = {"palette_hex", "tags_debug"}

DEFAULT_DATA = {
    "caption": "an image",
    "prompt": "placeholder",
    "negative_prompt": "low quality",
    "style": "anime",
    "model_suggestion": "unspecified",
    "params": {
        "width": 512,
        "height": 512,
        "steps": 20,
        "cfg_scale": 7.0,
        "sampler": "Euler",
        "seed": "random",
    },
    "control_suggestions": {
        "ip_adapter_reference": True,
        "openpose": False,
    },
    "meta": {
        "palette_hex": ["#000000"],
        "tags_debug": {},
    },
}


def validate_prompt(data: dict) -> None:
    """Validate required keys and value ranges."""

    missing = REQUIRED_TOP_LEVEL - data.keys()
    if missing:
        raise ValueError(f"missing keys: {sorted(missing)}")

    params = data.get("params", {})
    missing = REQUIRED_PARAMS - params.keys()
    if missing:
        raise ValueError(f"params missing keys: {sorted(missing)}")

    controls = data.get("control_suggestions", {})
    missing = REQUIRED_CONTROLS - controls.keys()
    if missing:
        raise ValueError(f"control_suggestions missing keys: {sorted(missing)}")

    meta = data.get("meta", {})
    missing = REQUIRED_META - meta.keys()
    if missing:
        raise ValueError(f"meta missing keys: {sorted(missing)}")

    # value checks
    for key in ["caption", "prompt", "negative_prompt", "style", "model_suggestion"]:
        if not isinstance(data.get(key), str) or not data[key]:
            raise ValueError(f"{key} must be a non-empty string")

    for key in ["width", "height", "steps", "cfg_scale"]:
        val = params.get(key)
        if not isinstance(val, (int, float)) or val <= 0:
            raise ValueError(f"param {key} must be positive number")
    if not isinstance(params.get("sampler"), str) or not params["sampler"]:
        raise ValueError("sampler must be non-empty string")
    if not isinstance(params.get("seed"), str) or not params["seed"]:
        raise ValueError("seed must be non-empty string")

    for key in REQUIRED_CONTROLS:
        if not isinstance(controls.get(key), bool):
            raise ValueError(f"control {key} must be boolean")

    palette = meta.get("palette_hex")
    if not isinstance(palette, list) or not palette or any(
        not isinstance(c, str) or not c for c in palette
    ):
        raise ValueError("palette_hex must be a non-empty list of strings")

    if not isinstance(meta.get("tags_debug"), dict):
        raise ValueError("tags_debug must be a dict")


def write_prompt(path: Path, data: dict) -> None:
    """Validate and write prompt data to JSON.

    If validation fails, default values are written instead to ensure no
    empty strings or zeroes remain.
    """

    try:
        validate_prompt(data)
        to_write = data
    except Exception as exc:  # pragma: no cover - fallback path
        logger.exception("Prompt validation failed: %s", exc)
        to_write = DEFAULT_DATA

    path = Path(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(to_write, f, ensure_ascii=False, indent=2)
