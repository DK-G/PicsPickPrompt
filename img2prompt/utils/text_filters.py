import re, unicodedata

NUMERIC_PAT = re.compile(r"^\d+$")

# --- 1) 人名判定：崩れ・typo・姓/名単体も検出 ---
ARTIST_FULL = {
    "ayami kojima",
    "rei hiroe",
    "shiori teshirogi",
    "tsugumi ohba",
    "tsukasa dokite",
    "omina tachibana",
    "kohei murata",
    "makoto shinkai",
    "erika ikuta",
    "harumi",
}
ARTIST_LAST = {
    "kojima",
    "hiroe",
    "teshirogi",
    "ohba",
    "dokite",
    "tachibana",
    "murata",
    "shinkai",
    "ikuta",
}
ARTIST_FIRST = {
    "ayami",
    "rei",
    "shiori",
    "tsugumi",
    "tsukasa",
    "omina",
    "kohei",
    "makoto",
    "erika",
    "harumi",
}

def _looks_like_artist(raw: str) -> bool:
    s = _nfkc_lower(raw)
    nos = s.replace(" ", "")
    # 1) 完全一致 / 空白除去一致
    if s in ARTIST_FULL or nos in {a.replace(" ", "") for a in ARTIST_FULL}:
        return True
    # 2) 語単位で姓/名が出たら“人名っぽい”
    words = set(s.split())
    if (words & ARTIST_LAST) or (words & ARTIST_FIRST):
        return True

    # 3) 軽微typo（距離<=2）でフルネームに近い
    def _lev2(a: str, b: str) -> int:
        if a == b:
            return 0
        if abs(len(a) - len(b)) > 2:
            return 3
        i = j = edits = 0
        while i < len(a) and j < len(b):
            if a[i] == b[j]:
                i += 1
                j += 1
            else:
                edits += 1
                if edits > 2:
                    return edits
                if len(a) == len(b):
                    i += 1
                    j += 1
                elif len(a) > len(b):
                    i += 1
                else:
                    j += 1
        edits += (len(a) - i) + (len(b) - j)
        return edits

    for full in ARTIST_FULL:
        if _lev2(nos, full.replace(" ", "")) <= 2:
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
META_EXACT = {
    "artist name",
    "twitter username",
    "page number",
    "general",
    "dated",
    "negative space",
    "text focus",
    "no humans",
    "multiple girls",
}
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

        if is_bad_token(t_raw):
            continue

        # 背景は1つだけ
        if "background" in t:
            if bg_kept:
                continue
            bg_kept = True

        if t not in seen:
            seen.add(t)
            out.append(t)
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
    """補完時にも再利用できる禁止語判定。まず“安全語は常に許可”。"""
    t = _nfkc_lower(raw or "")
    # ただしメタ語は必ず弾く
    if t in META_EXACT:
        return True

    # ✅ 先にホワイトリスト優先
    if (t in SAFE_EXACT) or any(k in t for k in SAFE_SUBSTR):
        return False

    # ❌ 通常のNG判定
    if not (2 <= len(t) <= 40):
        return True
    if NUMERIC_PAT.match(t):
        return True
    if _looks_like_artist(raw):
        return True
    if t in BAN_EXACT:
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


SAFE_FILL = [
    "portrait",
    "upper body",
    "looking at camera",
    "soft lighting",
    "warm tones",
    "sharp focus",
    "depth of field",
    "window light",
    "cozy atmosphere",
    "warm highlights",
    "gentle shadow",
    "natural skin tones",
    "ambient light",
    "balanced composition",
    "eye level view",
    "soft contrast",
    "realistic texture",
    "warm color palette",
    "fine details",
    "cinematic feel",
    "subtle bokeh",
    "subtle shadows",
    "smooth gradients",
    "natural highlights",
    "muted colors",
    "shallow depth",
    "soft focus",
    "clean background",
]


def finalize_prompt_safe(
    prompt_tags: list[str],
    min_total: int = 55,
    max_total: int = 70,
) -> list[str]:
    """Fill up missing slots with safe vocabulary only."""
    seen = set(prompt_tags)
    for w in SAFE_FILL:
        if len(prompt_tags) >= min_total:
            break
        if w not in seen:
            prompt_tags.append(w)
            seen.add(w)
    return prompt_tags[:max_total]

