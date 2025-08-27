import re
import unicodedata

# TitleCase 姓名検出
NAME_TITLECASE = re.compile(r"\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b")
NUMERIC_PAT = re.compile(r"^\d+$")

# 既知のアーティスト・人名（大文字小文字を問わず判定する）
ARTIST_TOKENS = {
    "Ayami Kojima","Rei Hiroe","Shiori Teshirogi","Tsugumi Ohba",
    "Tsukasa Dokite","Omina Tachibana","Kohei Murata",
    "Makoto Shinkai","Erika Ikuta","Harumi"
}
ARTIST_TOKENS_LOWER = {a.lower() for a in ARTIST_TOKENS}

# 線画/アニメ系ノイズ
BAN_SUBSTR = {
    "1girl","1boy","solo","comic","manga","cartoon",
    "lineart","sketch","monochrome","grayscale","greyscale","sensitive"
}

# メタ・文章系ノイズ
META_EXACT = {
    "artist name","twitter username","page number","general","dated",
}
BAN_PHRASES_SUBSTR = {
    "beautiful japanese girls face",
}

# 写真系ホワイトリスト（二語フレーズ）
SAFE_TWO_WORDS = {
    "upper body","soft lighting","warm tones","sharp focus","depth of field",
    "wooden interior","window light","cozy atmosphere","warm highlights",
    "gentle shadow","natural skin","ambient light","balanced composition",
    "eye level","soft contrast","realistic texture","color palette",
    "fine details","cinematic feel","subtle bokeh","clean background",
    "subtle shadows","smooth gradients","natural highlights","muted colors",
    "shallow depth","soft focus"
}

def _nfkc_lower(s: str) -> str:
    return unicodedata.normalize("NFKC", s).strip(" ,.;:").lower()

def _is_artist_like(raw: str) -> bool:
    raw_nfkc = unicodedata.normalize("NFKC", raw).strip()
    raw_lower = raw_nfkc.lower()
    nospace = raw_lower.replace(" ", "")

    if raw_lower in ARTIST_TOKENS_LOWER:
        return True
    if nospace in {a.replace(" ", "").lower() for a in ARTIST_TOKENS}:
        return True
    if NAME_TITLECASE.search(raw_nfkc):  # TitleCase 姓名
        return True
    return False

def clean_tokens(tokens):
    out, seen = [], set()
    background_seen = False

    for raw in tokens:
        if not raw:
            continue

        t_raw = raw.strip()
        t = _nfkc_lower(t_raw)
        safe = t in SAFE_TWO_WORDS

        if not safe:
            # ❌ 人名/作家名除去
            if _is_artist_like(t_raw):
                continue

            # ❌ 数値/短すぎ長すぎ
            if not (2 <= len(t) <= 40):
                continue
            if NUMERIC_PAT.match(t):
                continue

            # ❌ 線画/アニメ系ノイズ
            if any(b in t for b in BAN_SUBSTR):
                continue

            # ❌ メタ・文章系ノイズ
            if t in META_EXACT:
                continue
            if any(p in t for p in BAN_PHRASES_SUBSTR):
                continue

        # ❌ 背景タグは1つだけ残す
        if "background" in t:
            if background_seen:
                continue
            background_seen = True

        # ✅ 重複排除
        if t not in seen:
            seen.add(t); out.append(t)

    return out

