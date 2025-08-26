import argparse
from pathlib import Path

from .extract import blip, clip_interrogator, deepdanbooru
from .assemble import normalize, bucketize, palette, style
from .export import writer


def run(image_path: str) -> Path:
    image_path = Path(image_path)
    caption = blip.generate_caption(image_path)

    dd_tags = deepdanbooru.extract_tags(image_path)
    ci_tags = clip_interrogator.extract_tags(image_path)
    merged = normalize.merge_tags(dd_tags, ci_tags)
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
    prompt = ", ".join(ordered)

    style_name, params = style.determine_style(dd_tags, ci_tags)

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
            "tags_debug": {"deepdanbooru": dd_tags, "clip_interrogator": ci_tags},
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
