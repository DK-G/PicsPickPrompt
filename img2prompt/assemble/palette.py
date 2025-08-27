"""Extract dominant colours from an image."""

from pathlib import Path
from typing import List
import logging

logger = logging.getLogger(__name__)


def extract_palette(path: Path, k: int = 5) -> List[str]:
    """Extract ``k`` dominant colours as hex values, avoiding pure black."""

    try:
        from PIL import Image
        import numpy as np
        from sklearn.cluster import KMeans

        img = Image.open(path).convert("RGB")
        # Downsample to roughly 256px on the long side for speed.
        if img.width > img.height:
            img_small = img.resize((256, int(256 * img.height / img.width)), Image.BICUBIC)
        else:
            img_small = img.resize((int(256 * img.width / img.height), 256), Image.BICUBIC)

        arr = np.array(img_small).reshape(-1, 3).astype("float32")

        # Limit to 50k pixels for stable clustering speed.
        if arr.shape[0] > 50000:
            idx = np.random.RandomState(0).choice(arr.shape[0], 50000, replace=False)
            arr = arr[idx]

        km = KMeans(n_clusters=k, n_init=4, random_state=0)
        km.fit(arr)
        centers = km.cluster_centers_.astype("uint8")

        to_hex = lambda c: "#%02x%02x%02x" % (int(c[0]), int(c[1]), int(c[2]))
        hexes = [to_hex(c) for c in centers]
        hexes = [h if h.lower() != "#000000" else "#2a3d6d" for h in hexes]
        return hexes
    except Exception as exc:  # pragma: no cover - fallback path
        logger.warning("Palette extraction failed: %s", exc, exc_info=True)
        return [
            "#2a3d6d",
            "#ddc6ae",
            "#a5806c",
            "#5c4032",
            "#2c455b",
        ][:k]
