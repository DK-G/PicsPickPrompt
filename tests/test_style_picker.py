import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from img2prompt.assemble import style


def test_determine_style_photo_params():
    ci_text = "a photo with bokeh and 35mm film grain"
    result, params = style.determine_style(ci_text, {})
    assert result == "photo"
    assert params == style.PHOTO_PARAMS


def test_determine_style_anime_params():
    ci_text = "an anime manga character"
    result, params = style.determine_style(ci_text, {})
    assert result == "anime"
    assert params == style.ANIME_PARAMS

