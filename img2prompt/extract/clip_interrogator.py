from typing import Dict, List, Tuple
from PIL import Image
from clip_interrogator import Config, Interrogator
import re, logging, math
logger = logging.getLogger(__name__)

KEYS = [
    "lighting","light","bokeh","grain","35mm","cinematic","sharp focus",
    "depth of field","studio","natural","photograph","photography",
    "soft light","hard light","rim light","volumetric","backlight"
]

def _rank_phrases(raw: str, max_take: int = 20) -> List[str]:
    # ざっくりtf-idf風（長さと广杉性を重視）
    chunks = [c.strip().lower() for c in re.split(r"[,\n;/]", raw) if 2 <= len(c.strip()) <= 48]
    # フィルタ：英数・空白・ハイフンのみ通す
    chunks = [c for c in chunks if re.fullmatch(r"[a-z0-9 \-]+", c) is not None]
    # KEYSに触れているものは最優先
    keyed = [c for c in chunks if any(k in c for k in KEYS)]
    # スコア付け（単語数・ユニーク率）
    scores = {}
    for c in set(chunks):
        tokens = [t for t in c.split() if len(t) > 1]
        if not tokens: continue
        uniq = len(set(tokens)) / len(tokens)
        length = min(len(tokens), 6)
        bonus = 1.2 if c in keyed else 1.0
        scores[c] = (uniq * length) * bonus
    ranked = [c for c,_ in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)]
    # 最終 picks
    seen, picks = set(), []
    for c in ranked:
        if c not in seen:
            seen.add(c); picks.append(c)
        if len(picks) >= max_take:
            break
    return picks

def extract_tags(path) -> Tuple[Dict[str,float], List[str], str]:
    try:
        ci = Interrogator(Config())
        raw = ci.interrogate_fast(Image.open(path).convert("RGB"))
        raw_low = raw.lower()

        result: Dict[str,float] = {}
        # 1) 生テキスト由来の picks を作る
        picks = _rank_phrases(raw_low, max_take=20)
        # 2) 既存の候補語があれば優先スコア
        for c in picks:
            if any(k in c for k in KEYS):
                result[c] = max(result.get(c, 0.0), 0.55)
        # 3) KEYSを含まない句も0.50で採用（最低限語を確保）
        for c in picks:
            result.setdefault(c, 0.50)

        return result, picks[:20], raw
    except Exception as e:
        logger.warning("CLIP Interrogator failed: %s", e, exc_info=True)
        return {}, [], ""
