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
        wd14_tags_raw = wd14_onnx.extract_tags(image_path)
        wd14_tags = normalize.remove_placeholders(wd14_tags_raw)
        tags_debug["wd14_onnx"] = {"count": len(wd14_tags), "ok": True}
    except Exception as exc:  # pragma: no cover - should be rare
        logger.warning("WD14 extractor failed: %s", exc, exc_info=True)
        wd14_tags = {}
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

    merged = normalize.merge_tags(wd14_tags, dd_tags, ci_tags)
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

    merged_before = ordered
    prompt_tags = clean_tokens(merged_before)
    prompt_tags_final = bucketize.ensure_50_70(prompt_tags, caption, ci_picks)
    prompt = ", ".join(prompt_tags_final)

    style_name, params = style.determine_style(ci_raw, wd14_tags)

    print(
        f"[DEBUG] wd14_raw={len(wd14_tags_raw)} -> wd14_clean={len(wd14_tags)}; ci_raw_picks={len(ci_picks)}; "
        f"merged_before={len(merged_before)}; after_clean={len(prompt_tags)}; final={len(prompt_tags_final)}; style={style_name}"
    )

    data = {
        "caption": caption,
        "prompt": prompt,
        "negative_prompt": (
            "(low quality:1.2), (blurry:1.2), (jpeg artifacts:1.1), (duplicate:1.1), "
            "(bad anatomy:1.1), (extra fingers:1.2), (nsfw:1.3), (monochrome:1.1), (lineart:1.1)"
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
