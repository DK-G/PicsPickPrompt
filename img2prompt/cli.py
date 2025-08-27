import argparse
from pathlib import Path
import re
import logging

from .extract import blip, clip_interrogator, deepdanbooru, wd14_onnx
from .assemble import normalize, bucketize, palette, style
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
        ci_raw, ci_text, ci_fb = clip_interrogator.extract_tags(image_path)
        ci_tags = normalize.remove_placeholders(ci_raw)
        tags_debug["clip_interrogator"] = {
            "count": len(ci_tags),
            "ok": True,
            "fallback_chunks": ci_fb,
        }
    except Exception as exc:  # pragma: no cover - should be rare
        logger.warning("CLIP Interrogator extractor failed: %s", exc, exc_info=True)
        ci_tags, ci_text = {}, ""
        tags_debug["clip_interrogator"] = {
            "count": 0,
            "ok": False,
            "fallback_chunks": 0,
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

    def ensure_minimum_tags(existing, caption_text, ci_text_raw):
        STOP_WORDS = {
            "a",
            "an",
            "the",
            "at",
            "with",
            "of",
            "to",
            "in",
            "on",
            "for",
        }

        NAME_EXCEPTIONS = {
            "soft",
            "warm",
            "upper",
            "looking",
            "sharp",
            "depth",
            "wooden",
            "window",
            "natural",
            "studio",
            "light",
            "lighting",
            "focus",
            "body",
            "tones",
            "interior",
            "camera",
            "field",
            "bokeh",
            "grain",
            "cinematic",
            "portrait",
        }

        NAME_RE = re.compile(r"\b[a-z][a-z]+ [a-z][a-z]+\b", re.I)

        def looks_like_name(phrase: str) -> bool:
            if NAME_RE.fullmatch(phrase):
                parts = phrase.split()
                if not any(p in NAME_EXCEPTIONS for p in parts):
                    return True
            return False

        def clean_tokens(seq):
            cleaned = []
            for t in seq:
                t = re.sub(r",\s*", " ", t).strip().lower()
                while True:
                    parts = t.split()
                    if parts and parts[-1] in STOP_WORDS:
                        parts = parts[:-1]
                        t = " ".join(parts)
                    else:
                        break
                if not re.fullmatch(r"[a-z ]{2,48}", t):
                    continue
                if looks_like_name(t):
                    continue
                cleaned.append(t)
            return cleaned

        tags = clean_tokens(dict.fromkeys(existing))
        if len(tags) >= 50:
            return tags[:70]

        caption_text = caption_text.lower()
        caption_phrases = re.findall(r"[a-z]+(?: [a-z]+){0,3}", caption_text)
        for phrase in clean_tokens(caption_phrases):
            if phrase not in tags:
                tags.append(phrase)
            if len(tags) >= 50:
                break
        if len(tags) < 50:
            for chunk in re.split(r"[,\n]", ci_text_raw.lower()):
                for phrase in clean_tokens([chunk]):
                    if phrase not in tags:
                        tags.append(phrase)
                    if len(tags) >= 50:
                        break
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
                "wooden interior",
                "window light",
                "cozy atmosphere",
                "warm highlights",
                "gentle shadow",
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
