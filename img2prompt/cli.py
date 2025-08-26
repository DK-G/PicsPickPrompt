import argparse
import logging
from pathlib import Path

from .extract import florence, clip_interrogator, wd14
from .assemble import normalize, bucketize, palette
from .export import writer


logger = logging.getLogger(__name__)


def run(image_path: str) -> Path:
    image_path = Path(image_path)
    try:
        caption = florence.generate_caption(image_path)
        if not caption:
            logger.warning("Caption generation returned empty for %s", image_path)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Caption generation failed for %s: %s", image_path, exc)
        caption = ""

    tags: list[str] = []
    for extractor in (clip_interrogator.extract_tags, wd14.extract_tags):
        try:
            tags.extend(extractor(image_path))
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("%s failed for %s: %s", extractor.__name__, image_path, exc)
    if not tags:
        logger.warning("No tags extracted for %s", image_path)

    try:
        tags = normalize.normalize_tags(tags)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Tag normalization failed for %s: %s", image_path, exc)
        tags = []
    try:
        buckets = bucketize.bucketize(tags)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Bucketizing tags failed for %s: %s", image_path, exc)
        buckets = {}

    ordered: list[str] = []
    for key in ["subject", "appearance", "scene", "composition", "style_lighting"]:
        ordered.extend(buckets.get(key, []))
    if not ordered:
        logger.warning("No ordered tags produced for %s", image_path)
    prompt = ", ".join(ordered)
    if not prompt:
        logger.warning("Prompt is empty for %s", image_path)

    try:
        palette_hex = palette.extract_palette(image_path)
        if not palette_hex:
            logger.warning("Palette extraction returned no colours for %s", image_path)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Palette extraction failed for %s: %s", image_path, exc)
        palette_hex = []

    data = {
        "caption": caption,
        "prompt": prompt,
        "negative_prompt": "low quality, worst quality, blurry, jpeg artifacts, watermark, text, extra fingers, deformed hands, bad anatomy",
        "style": "anime",
        "model_suggestion": "",
        "params": {
            "width": 0,
            "height": 0,
            "steps": 0,
            "cfg_scale": 0,
            "sampler": "",
            "seed": "random",
        },
        "control_suggestions": {
            "ip_adapter_reference": False,
            "openpose": False,
        },
        "meta": {
            "palette_hex": palette_hex,
            "tags_debug": {"stub": {t: 1.0 for t in ordered}},
        },
    }
    out_path = image_path.with_name(image_path.name + ".prompt.json")
    try:
        writer.write_prompt(out_path, data)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Failed to write prompt for %s: %s", image_path, exc)
        raise
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate prompt JSON from an image")
    parser.add_argument("image", help="Path to input image")
    args = parser.parse_args()
    out = run(args.image)
    print(out)


if __name__ == "__main__":
    main()
