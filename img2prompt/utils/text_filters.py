import re, unicodedata
import difflib

NUMERIC_PAT = re.compile(r"^\d+$")

# --- 1) 人名判定（フルネーム一致のみ） ---
# --- 1) 人名判定 ------------------------------------------------------------
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

_DEFUSE = {a.replace(" ", "") for a in ARTIST_FULL}

def _similar(a: str, b: str) -> float:
    return difflib.SequenceMatcher(a=a, b=b).ratio()

def _looks_like_artist(raw: str) -> bool:
    s = _nfkc_lower(raw)              # 既存の正規化: NFKC + lower + trim を想定
    nos = s.replace(" ", "")

    # 完全一致
    if s in ARTIST_FULL or nos in _DEFUSE:
        return True

    # 近似一致（1〜2文字崩れを検知）
    for full in ARTIST_FULL:
        if _similar(nos, full.replace(" ", "")) >= 0.84:
            return True

    # 姓名の片側一致 + もう片側が高類似
    parts = s.split()
    if len(parts) == 2 and (ARTIST_FIRST or ARTIST_LAST):
        f, l = parts
        if (l in ARTIST_LAST and ARTIST_FIRST and
            max(_similar(f, x) for x in ARTIST_FIRST) >= 0.90):
            return True
        if (f in ARTIST_FIRST and ARTIST_LAST and
            max(_similar(l, x) for x in ARTIST_LAST) >= 0.90):
            return True

    # 追加: 単語単体でも既知の名簿にあれば弾く
    if (s in ARTIST_FIRST) or (s in ARTIST_LAST):
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
    "natural highlights","muted colors","shallow depth","soft focus","clean background",
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

# --- 新規: 人名断片のパージ -----------------------------------------------
def purge_artist_fragments(tokens: list[str],
                           blocked_fullnames: set[str] | None = None,
                           first_names: set[str] | None = None,
                           last_names: set[str] | None = None) -> list[str]:
    """
    既に 'blocked_in_ensure' 相当で弾かれた複合名の
    構成要素（例: 'ayami kojima' -> {'ayami','kojima'}）や
    既知の FIRST/LAST 名簿の単語を、単体出現していたら削除する。
    """
    blocked_fullnames = blocked_fullnames or set()
    first_names = first_names or (ARTIST_FIRST if 'ARTIST_FIRST' in globals() else set())
    last_names  = last_names  or (ARTIST_LAST  if 'ARTIST_LAST'  in globals() else set())

    # 複合名の構成要素（空白区切り）を抽出
    parts = set()
    for full in blocked_fullnames:
        for p in full.split():
            p = _nfkc_lower(p).strip()
            if p:
                parts.add(p)

    # 既知の名簿も対象に
    parts |= { _nfkc_lower(x).strip() for x in first_names | last_names }

    # 軽いホワイトリスト（誤爆を避けたい一般語）
    WHITELIST = {"maya","max","arnold","blender","unity","unreal"}
    parts -= WHITELIST

    # トークンをパージ
    out = []
    for t in tokens:
        tt = _nfkc_lower(t).strip()
        if tt in parts:
            continue
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


def drop_contradictions(tags: list[str]) -> list[str]:
    """明らかな矛盾（長短や有無の衝突）を簡易に解消する。"""
    s = set(t.strip() for t in tags)

    # 髪の長さ
    hair = {"long hair","short hair","very short hair","medium hair"}
    both_hair = s & hair
    if len(both_hair) >= 2:
        s -= hair  # ニュートラルへ

    # 追加したい矛盾ルールがあればここに追記
    # 例: "open mouth" と "closed mouth" 等
    mouth = {"open mouth","closed mouth"}
    both_mouth = s & mouth
    if len(both_mouth) >= 2:
        s -= mouth

    return [t for t in tags if t in s]


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
    # subject / framing
    "portrait","upper body","bust shot","three-quarter view","eye level view",
    "rule of thirds","balanced composition","centered composition","leading lines",
    "negative space balance","tight framing","loose framing",

    # camera / optics
    "looking at camera","soft focus","sharp focus","selective focus",
    "depth of field","shallow depth","wide aperture","narrow aperture",
    "natural perspective","standard lens look",

    # lighting
    "soft lighting","window light","ambient light","fill light feel",
    "rim light hint","backlight glow","warm highlights","gentle shadow",
    "soft contrast","low contrast look","subtle shadows","natural highlights",

    # color / tone
    "warm tones","muted colors","warm color palette","neutral palette",
    "smooth gradients","realistic texture","fine details","true-to-life color",
    "cinematic feel","subtle bokeh","creamy bokeh",

    # environment-neutral (背景に依存しない)
    "clean background","uncluttered background","simple backdrop","soft backdrop",
    "cozy atmosphere","calm atmosphere","intimate mood","natural skin tones",
    "even illumination","tone balance","gentle falloff","soft vignette",

    # micro look & finish
    "micro contrast","surface detail","skin texture retained","tone mapping gentle",
    "color harmony","midtone richness","highlight rolloff",

    # scene neutrals（今回のサンプルにも親和）
    "wooden interior","window light pattern","indoor ambience","evening warmth",

    # stability boosters
    "subtle color variation","fine grain feel","minimal noise",
    "clean rendition","photographic realism","life-like rendering","studio quality feel",

    # compositional helpers
    "eye contact","head-and-shoulders framing","comfortable spacing",
    "subject isolation","foreground separation","background separation",

    # safety extras（重複はdedupeで整理）
    "soft tonality","gentle tonality","organic look","true-to-tone rendering",
    "quiet color scheme","balanced exposure","graded warmth","subtle glow",

    # last-mile fillers
    "refined detail","smooth tonal range","nuanced lighting","depth cueing",
    "visual coherence","polished finish","natural rendition","clean presentation",
]


MIN_TOKENS = 55
MAX_TOKENS = 65


def finalize_prompt_safe(
    prompt_tags: list[str],
    min_total: int = MIN_TOKENS,
    max_total: int = MAX_TOKENS,
) -> list[str]:
    """Fill up missing slots with safe vocabulary only."""
    seen = set(prompt_tags)
    bg_present = any("background" in t for t in prompt_tags)
    for w in SAFE_FILL:
        if len(prompt_tags) >= min_total:
            break
        if w in seen:
            continue
        if bg_present and "background" in w:
            continue
        prompt_tags.append(w)
        seen.add(w)
    return prompt_tags[:max_total]


def finalize_pipeline(tokens: list[str], blocked_names: set[str] | None = None) -> list[str]:
    tokens = normalize_terms(tokens)
    tokens = dedupe_background(tokens)
    tokens = drop_contradictions(tokens)

    # ← ここで「人名断片」を掃除
    tokens = purge_artist_fragments(tokens, blocked_fullnames=blocked_names)

    tokens = finalize_prompt_safe(tokens, min_total=MIN_TOKENS, max_total=MAX_TOKENS)
    tokens = dedupe_background(tokens)  # 埋め戻しで背景語が再増殖した場合の最終整理
    if len(tokens) < MIN_TOKENS:
        tokens = finalize_prompt_safe(tokens, min_total=MIN_TOKENS, max_total=MAX_TOKENS)
        tokens = dedupe_background(tokens)
    return tokens

