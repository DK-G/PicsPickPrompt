import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from img2prompt.assemble import style


def test_determine_style_photo_params():
    dd_tags = {f"tag{i}": 1.0 for i in range(40)}
    ci_tags = {"35mm": 1.0}
    result, params = style.determine_style(dd_tags, ci_tags)
    assert result == "photo"
    assert params == style.PHOTO_PARAMS


def test_determine_style_anime_params():
    dd_tags = {f"tag{i}": 1.0 for i in range(40)}
    ci_tags = {}
    result, params = style.determine_style(dd_tags, ci_tags)
    assert result == "anime"
    assert params == style.ANIME_PARAMS

