import json
from pathlib import Path

# The real project uses the ``jsonschema`` package for validation, but the
# execution environment for these exercises has no network access, which
# makes installing third party dependencies difficult.  To keep the sample
# self-contained we perform a very small amount of manual validation instead.

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


def validate_prompt(data: dict) -> None:
    """Very small validator ensuring required keys, types and ranges."""

    missing = REQUIRED_TOP_LEVEL - data.keys()
    if missing:
        raise ValueError(f"missing keys: {sorted(missing)}")

    for key in ["caption", "prompt", "negative_prompt", "style", "model_suggestion"]:
        if not isinstance(data.get(key), str):
            raise ValueError(f"{key} must be a string")

    params = data.get("params", {})
    missing = REQUIRED_PARAMS - params.keys()
    if missing:
        raise ValueError(f"params missing keys: {sorted(missing)}")
    for key in ["width", "height", "steps", "cfg_scale"]:
        value = params.get(key)
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"params.{key} must be a non-negative int")
    if not isinstance(params.get("sampler"), str):
        raise ValueError("params.sampler must be a string")
    if not isinstance(params.get("seed"), (str, int)):
        raise ValueError("params.seed must be a string or int")

    controls = data.get("control_suggestions", {})
    missing = REQUIRED_CONTROLS - controls.keys()
    if missing:
        raise ValueError(f"control_suggestions missing keys: {sorted(missing)}")
    for key in REQUIRED_CONTROLS:
        if not isinstance(controls.get(key), bool):
            raise ValueError(f"control_suggestions.{key} must be a boolean")

    meta = data.get("meta", {})
    missing = REQUIRED_META - meta.keys()
    if missing:
        raise ValueError(f"meta missing keys: {sorted(missing)}")
    if not isinstance(meta.get("palette_hex"), list):
        raise ValueError("meta.palette_hex must be a list")
    if not isinstance(meta.get("tags_debug"), dict):
        raise ValueError("meta.tags_debug must be a dict")


def write_prompt(path: Path, data: dict) -> None:
    """Validate and write prompt data to JSON."""

    validate_prompt(data)
    path = Path(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
