"""Placeholder WD14 tag extraction."""

from pathlib import Path
from typing import List


def extract_tags(path: Path) -> List[str]:
    """Return example tags that WD14 might produce.

    A real implementation would load the ConvNeXtV2 based tagger and
    perform inference on ``path``.  Here we simply return a short list of
    deterministic tags to keep the example lightweight.
    """

    return ["1girl", "smile", "blue eyes", "brown hair"]

