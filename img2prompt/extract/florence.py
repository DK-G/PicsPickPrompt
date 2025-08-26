"""Placeholder caption extraction using Florence-2."""

from pathlib import Path


def generate_caption(path: Path) -> str:
    """Return a stand-in caption for the image.

    The real project would invoke a Florence-2 model to produce a rich
    description.  For the purposes of the kata we simply return a fixed
    string so the rest of the pipeline can be exercised without heavy
    dependencies.
    """

    return "a detailed caption from Florence-2"

