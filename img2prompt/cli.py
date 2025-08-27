import argparse
from pathlib import Path
import logging

from .extract import blip, clip_interrogator, deepdanbooru, wd14_onnx
from .assemble import normalize, bucketize, palette, style
from .utils.text_filters import clean_tokens
from .export import writer

logger = logging.getLogger(__name__)


def run(image_path: str) -> Path:
    image_path = Path(image_path)
    caption = blip.generate_caption(image_path)

    # --- tag extraction with error capture
    tags_debug = {}

    try:
        wd_raw = wd14_onnx.extract_tags(image_path)
        wd_tags = normalize.remove_placeholders(wd_raw)
        tags_debug["wd14_onnx"] = {"count": len(wd_tags), "ok": True}
    except Exception as exc:  # pragma: no cover - should be rare
        logger.warning("WD14 extractor failed: %s", exc, exc_info=True)
        wd_tags = {}
        tags_debug["wd14_onnx"] = {"count": 0, "ok": False, "error": str(exc)}

    try:
        dd_raw, dd_err = deepdanbooru.extract_tags(image_path)
        dd_tags = normalize.remove_placeholders(dd_raw)
        dbg = {"count": len(dd_tags), "ok": dd_err is None}
        if dd_err:
            dbg["error"] = dd_err
        tags_debug["deepdanbooru"] = dbg
    except Exception as exc:  # pragma: no cover - should be rare
        logger.warning("DeepDanbooru extractor failed: %s", exc, exc_info=True)
        dd_tags = {}
        tags_debug["deepdanbooru"] = {"count": 0, "ok": False, "error": str(exc)}

    try:
        ci_tags, ci_picks, ci_raw = clip_interrogator.extract_tags(image_path)
        ci_tags = normalize.remove_placeholders(ci_tags)
        tags_debug["clip_interrogator"] = {"count": len(ci_tags), "ok": True}
    except Exception as exc:  # pragma: no cover - should be rare
        logger.warning("CLIP Interrogator extractor failed: %s", exc, exc_info=True)
        ci_tags, ci_picks, ci_raw = {}, [], ""
        tags_debug["clip_interrogator"] = {
            "count": 0,
            "ok": False,
            "error": str(exc),
        }

    merged = normalize.merge_tags(wd_tags, dd_tags, ci_tags)
    buckets = bucketize.bucketize(merged)

    ordered = []
    for key in [
        "subject",
        "appearance",
        "scene",
        "composition",
        "style_lighting",
        "extra",
    ]:
        ordered.extend(buckets.get(key, []))

    prompt_tags = bucketize.ensure_50_70(ordered, caption, ci_picks)
    prompt_tags = clean_tokens(prompt_tags)
    prompt = ", ".join(prompt_tags)

    style_name, params = style.determine_style(ci_raw, wd_tags)

    print(
        f"[DEBUG] wd14={len(wd_tags)}, dd={len(dd_tags)}, ci={len(ci_tags)}, "
        f"final={len(prompt_tags)}, style={style_name}"
    )

    data = {
        "caption": caption,
        "prompt": prompt,
        "negative_prompt": (
            "low quality, worst quality, blurry, jpeg artifacts, watermark, text, extra fingers, deformed hands, bad anatomy"
        ),
        "style": style_name,
        "model_suggestion": "unspecified",
        "params": params,
        "control_suggestions": {
            "ip_adapter_reference": True,
            "openpose": False,
        },
        "meta": {
            "palette_hex": palette.extract_palette(image_path),
            "tags_debug": tags_debug,
        },
    }
    out_path = image_path.with_name(image_path.name + ".prompt.json")
    writer.write_prompt(out_path, data)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate prompt JSON from an image")
    parser.add_argument("image", help="Path to input image")
    args = parser.parse_args()
    out = run(args.image)
    print(out)


if __name__ == "__main__":
    main()
