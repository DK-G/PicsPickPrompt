import argparse
from pathlib import Path

from .extract import florence, clip_interrogator, wd14
from .assemble import normalize, bucketize, palette
from .export import writer


def run(image_path: str) -> Path:
    image_path = Path(image_path)
    caption = florence.generate_caption(image_path)
    tags = []
    tags.extend(clip_interrogator.extract_tags(image_path))
    tags.extend(wd14.extract_tags(image_path))
    tags = normalize.normalize_tags(tags)
    buckets = bucketize.bucketize(tags)
    ordered = []
    for key in ["subject", "appearance", "scene", "composition", "style_lighting"]:
        ordered.extend(buckets.get(key, []))
    prompt = ", ".join(ordered)
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
            "palette_hex": palette.extract_palette(image_path),
            "tags_debug": {"stub": {t: 1.0 for t in ordered}},
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
