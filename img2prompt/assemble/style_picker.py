from typing import Iterable

ANIME_KEYWORDS = {"anime", "manga", "cartoon"}


def pick_style(tags: Iterable[str]) -> str:
    """Return ``"anime"`` if tags hint at animation, else ``"photo"``."""
    for tag in tags:
        lower = tag.lower()
        if any(keyword in lower for keyword in ANIME_KEYWORDS):
            return "anime"
    return "photo"
