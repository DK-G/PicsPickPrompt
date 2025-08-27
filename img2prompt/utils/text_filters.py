import unicodedata, re

# TitleCase 姓名検出
NAME_TITLECASE = re.compile(r"\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b")
NUMERIC_PAT = re.compile(r"^\d+$")

# 既知のアーティスト・人名（大文字小文字や空白崩れを許容）
ARTIST_TOKENS = {
    "Ayami Kojima","Rei Hiroe","Shiori Teshirogi","Tsugumi Ohba",
    "Tsukasa Dokite","Omina Tachibana","Kohei Murata",
    "Makoto Shinkai","Erika Ikuta","Harumi"
}
# 小文字・空白除去済みの比較セット
_ART_LOWER_NOWS = {
    unicodedata.normalize("NFKC", a).lower().replace(" ", "")
    for a in ARTIST_TOKENS
}

# 線画/アニメ系ノイズ
BAN_SUBSTR = {
    "comic","manga","cartoon",
    "lineart","sketch","monochrome","grayscale","greyscale","sensitive"
}

# メタ・文章系ノイズ
META_EXACT = {
    "artist name","twitter username","page number","general","dated",
    "text focus","no humans","multiple girls",
}
BAN_PHRASES_SUBSTR = {
    "beautiful japanese girls face",
}
BAN_EXACT = {"standing","solo","1girl","1boy"}

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

def _lev(a: str, b: str) -> int:
    la, lb = len(a), len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la
    prev = list(range(lb + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * lb
        for j, cb in enumerate(b, 1):
            ins = cur[j - 1] + 1
            delete = prev[j] + 1
            replace = prev[j - 1] + (ca != cb)
            cur[j] = min(ins, delete, replace)
        prev = cur
    return prev[lb]


def _looks_like_artist(raw: str) -> bool:
    s = unicodedata.normalize("NFKC", raw).lower()
    nos = s.replace(" ", "")
    if nos in _ART_LOWER_NOWS:
        return True
    for tgt in _ART_LOWER_NOWS:
        if abs(len(nos) - len(tgt)) <= 2 and _lev(nos, tgt) <= 2:
            return True
    return bool(NAME_TITLECASE.search(raw))

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
            if _looks_like_artist(t_raw):
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
            if t in BAN_EXACT:
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

