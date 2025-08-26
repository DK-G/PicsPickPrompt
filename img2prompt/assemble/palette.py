from itertools import cycle
from pathlib import Path
from typing import List

from PIL import Image

FALLBACK_COLORS = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#00ffff"]


def extract_palette(path: Path, colors: int = 5) -> List[str]:
    """Extract a simple colour palette from ``path``.

    The implementation intentionally avoids heavy dependencies and instead
    uses ``Pillow`` to count colours in a downscaled version of the image.
    Any ``#000000`` entries are replaced with fallback colours to ensure the
    result contains non-black values only.
    """

    img = Image.open(path).convert("RGB")
    small = img.resize((64, 64))
    color_counts = small.getcolors(64 * 64) or []
    color_counts.sort(reverse=True)
    hexes: List[str] = []
    for count, (r, g, b) in color_counts[:colors]:
        hexes.append(f"#{r:02x}{g:02x}{b:02x}")

    hexes = [c for c in hexes if c.lower() != "#000000"]
    filler = cycle(FALLBACK_COLORS)
    while len(hexes) < colors:
        candidate = next(filler)
        if candidate not in hexes:
            hexes.append(candidate)
    return hexes[:colors]
