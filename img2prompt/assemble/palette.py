from pathlib import Path
from typing import List


def extract_palette(path: Path, colors: int = 5) -> List[str]:
    """Return a placeholder palette.

    The real project would analyse the image to produce dominant colours,
    but to keep the prototype lightweight and dependency free we simply
    return a list of ``"#000000"`` entries with the requested length.
    """

    return ["#000000" for _ in range(colors)]
