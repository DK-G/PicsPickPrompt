"""Extract dominant colours from an image."""

from pathlib import Path
from typing import List
import logging

logger = logging.getLogger(__name__)


def extract_palette(path: Path, colors: int = 5) -> List[str]:
    """Return a list of dominant colours in hexadecimal form.

    If processing fails, a list of ``"#000000"`` entries is returned.
    """

    try:
        from PIL import Image
        import numpy as np
        from sklearn.cluster import KMeans

        image = Image.open(path).convert("RGB")
        arr = np.array(image).reshape(-1, 3)
        kmeans = KMeans(n_clusters=colors, n_init=10)
        kmeans.fit(arr)
        centres = kmeans.cluster_centers_.astype(int)
        hexes = ["#{:02x}{:02x}{:02x}".format(*c) for c in centres]
        return hexes
    except Exception as exc:  # pragma: no cover - fallback path
        logger.exception("Palette extraction failed: %s", exc)
        return ["#000000" for _ in range(colors)]
