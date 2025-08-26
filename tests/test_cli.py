import json
from pathlib import Path

from PIL import Image

from img2prompt import cli
from img2prompt.export import writer


def create_image(path: Path) -> None:
    Image.new("RGB", (64, 64), color="red").save(path)


def test_cli_generates_valid_prompt(tmp_path):
    img_path = tmp_path / "test.jpg"
    create_image(img_path)
    out = cli.run(str(img_path))
    data = json.loads(Path(out).read_text())
    writer.validate_prompt(data)

    tags = [t.strip() for t in data["prompt"].split(",")]
    assert 50 <= len(tags) <= 70
    assert all("subject_extra_" not in t and "extra_tag_" not in t for t in tags)

    assert data["style"] == "anime"

    params = data["params"]
    assert params["width"] > 0
    assert params["height"] > 0
    assert params["steps"] > 0
    assert params["cfg_scale"] > 0
    assert params["sampler"]

    palette = data["meta"]["palette_hex"]
    assert len(palette) == 5
    assert all(c.lower() != "#000000" for c in palette)


def test_cli_style_photo_when_no_wd14_tags(tmp_path, monkeypatch):
    img_path = tmp_path / "photo.jpg"
    create_image(img_path)

    monkeypatch.setattr(cli.wd14, "extract_tags", lambda p: [])

    out = cli.run(str(img_path))
    data = json.loads(Path(out).read_text())
    assert data["style"] == "photo"
