import re, unicodedata

NUMERIC_PAT = re.compile(r"^\d+$")

# --- 1) 人名判定：小文字・空白崩れ・軽微typoのみ（過剰マッチ防止のため距離≤1） ---
ARTIST_TOKENS = {
    "Ayami Kojima","Rei Hiroe","Shiori Teshirogi","Tsugumi Ohba",
    "Tsukasa Dokite","Omina Tachibana","Kohei Murata",
    "Makoto Shinkai","Erika Ikuta","Harumi",
    # 単語だけで来るケースも弾く
    "Ayami","Kojima","Ohba","Teshirogi","Hiroe","Dokite","Tachibana","Ikuta","Shinkai",
}
_ART_NOWS = {unicodedata.normalize("NFKC", a).lower().replace(" ", "") for a in ARTIST_TOKENS}

def _lev1(a: str, b: str) -> bool:
    # レーベンシュタイン距離 ≤1（高速・過剰除外を避ける）
    if a == b:
        return True
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        diff = [(x, y) for x, y in zip(a, b) if x != y]
        if len(diff) == 1:
            return True  # 置換1回
        if len(diff) == 2 and diff[0][0] == diff[1][1] and diff[0][1] == diff[1][0]:
            return True  # 2文字の入れ替え
        return False
    # 長さ差1の場合: 挿入/削除1回
    if len(a) < len(b):
        a, b = b, a
    i = j = edits = 0
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            i += 1; j += 1
        else:
            edits += 1
            if edits > 1:
                return False
            i += 1  # aが長いので削除
    return True

def _looks_like_artist(raw: str) -> bool:
    s = unicodedata.normalize("NFKC", raw).lower()
    nos = s.replace(" ", "")
    if nos in _ART_NOWS:
        return True
    # 軽微typoのみ許容（距離≤1）
    for tgt in _ART_NOWS:
        if _lev1(nos, tgt):
            return True
    return False

# --- 2) 写真語ホワイトリスト（先に通す） ---
SAFE_SUBSTR = {
    "lighting","bokeh","focus","depth of field","window light","eye level",
    "warm tones","skin tones","highlights","shadows","gradients","texture",
    "contrast","composition","cinematic","realistic","color palette",
    "upper body","looking at camera","cozy atmosphere","wooden interior",
}
SAFE_EXACT = {
    "portrait","upper body","looking at camera","soft lighting","warm tones",
    "sharp focus","depth of field","window light","cozy atmosphere","warm highlights",
    "gentle shadow","natural skin tones","ambient light","balanced composition",
    "eye level view","soft contrast","realistic texture","warm color palette",
    "fine details","cinematic feel","subtle bokeh","subtle shadows","smooth gradients",
    "natural highlights","muted colors","shallow depth","soft focus",
}

# --- 3) 落とす語（最小限&明示） ---
BAN_SUBSTR = {
    "comic","manga","cartoon","lineart","sketch","monochrome","grayscale","greyscale","sensitive",
}
BAN_EXACT = {"standing","solo","1girl","1boy"}
META_EXACT = {"artist name","twitter username","page number","general","dated","negative space"}
BAN_PHRASES_SUBSTR = {"beautiful japanese girls face"}

def _nfkc_lower(s: str) -> str:
    return unicodedata.normalize("NFKC", s).strip(" ,.;:").lower()

def clean_tokens(tokens):
    out, seen = [], set()
    bg_kept = False

    for raw in tokens:
        if not raw: 
            continue
        t_raw = raw.strip()
        t = _nfkc_lower(t_raw)

        # ✅ 先にホワイトリスト（写真語）は無条件通過（人名判定より先！）
        if (t in SAFE_EXACT) or any(key in t for key in SAFE_SUBSTR):
            if t not in seen:
                seen.add(t); out.append(t)
            continue

        # ❌ 人名（軽微typo含む）
        if _looks_like_artist(t_raw):
            continue

        # ❌ 数値/長さ
        if not (2 <= len(t) <= 40): 
            continue
        if NUMERIC_PAT.match(t):
            continue

        # ❌ アニメ/線画系
        if any(b in t for b in BAN_SUBSTR):
            continue

        # ❌ メタ・文章・カウント
        if t in META_EXACT or t in BAN_EXACT:
            continue
        if any(p in t for p in BAN_PHRASES_SUBSTR):
            continue

        # ❌ 背景は1つだけ
        if "background" in t:
            if bg_kept:
                continue
            bg_kept = True

        if t not in seen:
            seen.add(t); out.append(t)
    return out

# --- 4) ensure_50_70の後に背景重複を最終整理（補完で再注入された分を落とす） ---
def dedupe_background(tags):
    out, seen_bg = [], False
    for t in tags:
        if "background" in t:
            if seen_bg:
                continue
            seen_bg = True
        out.append(t)
    return out


def is_bad_token(raw: str) -> bool:
    t = _nfkc_lower(raw or "")
    if not (2 <= len(t) <= 40):
        return True
    if NUMERIC_PAT.match(t):
        return True
    if _looks_like_artist(raw):
        return True
    if t in META_EXACT or t in BAN_EXACT:
        return True
    if any(p in t for p in BAN_PHRASES_SUBSTR):
        return True
    if any(b in t for b in BAN_SUBSTR):
        return True
    return False


NORMALIZE_MAP = {
    "looking at viewer": "looking at camera",
    "eye level": "eye level view",
    "white background": "clean background",
    "grey background": "clean background",
    "simple background": "clean background",
}


def normalize_terms(tags: list[str]) -> list[str]:
    out, seen = [], set()
    for t in tags:
        t2 = NORMALIZE_MAP.get(t, t)
        if t2 not in seen:
            seen.add(t2)
            out.append(t2)
    return out

