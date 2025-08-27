import json
import sys
from pathlib import Path
import string

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from img2prompt import cli


def test_cli_generates_clean_output(tmp_path, monkeypatch):
    # Prepare dummy image path
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"fake")

    # Stub model outputs
    monkeypatch.setattr(cli.blip, "generate_caption", lambda p: "a caption")

    letters = string.ascii_lowercase

    def alpha_tag(i: int) -> str:
        return "tag" + letters[i % 26] + letters[(i // 26) % 26]

    wd_tags = {alpha_tag(i): 1.0 for i in range(20)}
    monkeypatch.setattr(cli.wd14_onnx, "extract_tags", lambda p: wd_tags)

    dd_tags = {alpha_tag(i): 1.0 for i in range(20, 40)}
    dd_tags["subject_extra_1"] = 0.9
    monkeypatch.setattr(cli.deepdanbooru, "extract_tags", lambda p: dd_tags)

    ci_tags = {alpha_tag(i): 0.5 for i in range(40, 80)}
    ci_tags["extra_tag_1"] = 0.8
    monkeypatch.setattr(
        cli.clip_interrogator,
        "extract_tags",
        lambda p: (ci_tags, "soft lighting, 35mm", 0),
    )

    monkeypatch.setattr(
        cli.palette,
        "extract_palette",
        lambda p: ["#010101", "#020202", "#030303", "#040404", "#050505"],
    )

    out = cli.run(str(img_path))
    data = json.loads(Path(out).read_text("utf-8"))

    tags = [t.strip() for t in data["prompt"].split(",") if t.strip()]
    assert 50 <= len(tags) <= 70
    assert all(
        not t.startswith("subject_extra_") and not t.startswith("extra_tag_")
        for t in tags
    )
    assert all(c != "#000000" for c in data["meta"]["palette_hex"])
    dbg = data["meta"]["tags_debug"]
    assert dbg["deepdanbooru"]["count"] == 20
    assert dbg["deepdanbooru"]["ok"] is True
    assert dbg["clip_interrogator"]["count"] == 40
    assert dbg["clip_interrogator"]["ok"] is True
    assert dbg["clip_interrogator"]["fallback_chunks"] == 0
    assert dbg["wd14_onnx"]["count"] == 20
    assert dbg["wd14_onnx"]["ok"] is True
    assert data["style"] in {"anime", "photo"}
    params = data["params"]
    for key in ["width", "height", "steps", "cfg_scale"]:
        assert params[key] > 0
    assert params["sampler"]
