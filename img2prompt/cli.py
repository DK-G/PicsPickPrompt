import argparse
from pathlib import Path
import re

from .extract import blip, clip_interrogator, deepdanbooru, wd14_onnx
from .assemble import normalize, bucketize, palette, style
from .export import writer


def run(image_path: str) -> Path:
    image_path = Path(image_path)
    caption = blip.generate_caption(image_path)

    wd_raw = wd14_onnx.extract_tags(image_path)
    dd_raw = deepdanbooru.extract_tags(image_path)
    ci_raw, ci_text = clip_interrogator.extract_tags(image_path)

    wd_tags = normalize.remove_placeholders(wd_raw)
    dd_tags = normalize.remove_placeholders(dd_raw)
    ci_tags = normalize.remove_placeholders(ci_raw)

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

    def ensure_minimum_tags(existing, caption_text, ci_text_raw):
        tags = list(dict.fromkeys(existing))
        if len(tags) >= 50:
            return tags[:70]
        caption_text = caption_text.lower()
        for phrase in re.findall(r"[a-z]+(?: [a-z]+){0,3}", caption_text):
            if phrase not in tags:
                tags.append(phrase)
            if len(tags) >= 50:
                break
        if len(tags) < 50:
            for chunk in re.split(r"[,\n]", ci_text_raw.lower()):
                w = chunk.strip()
                if w and w not in tags:
                    tags.append(w)
                if len(tags) >= 50:
                    break
        if len(tags) < 50:
            fallback = [
                "portrait",
                "upper body",
                "looking at camera",
                "soft lighting",
                "warm tones",
                "sharp focus",
                "depth of field",
            ]
            for w in fallback:
                if w not in tags:
                    tags.append(w)
                if len(tags) >= 50:
                    break
        return tags[:70]

    ordered = ensure_minimum_tags(ordered, caption, ci_text)
    prompt = ", ".join(ordered)

    style_name, params = style.determine_style(ci_text)

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
            "tags_debug": {
                "wd14_onnx": wd_tags,
                "deepdanbooru": dd_tags,
                "clip_interrogator": ci_tags,
            },
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
