import re, unicodedata
import difflib
import random
import hashlib
from typing import Iterable, Sequence

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


BG_GROUPS = [
    {
        "clean background",
        "uncluttered background",
        "simple background",
        "simple backdrop",
        "soft backdrop",
        "plain background",
        "blank background",
    }
]


def unify_background(tokens: list[str]) -> list[str]:
    keep = set(t.lower().strip() for t in tokens)
    for group in BG_GROUPS:
        if keep & group:
            keep -= group
            keep.add("clean background")
    return [t for t in tokens if t.lower().strip() in keep]

# 画角ベースで下半身系タグを除去
UPPER_BODY_CUES = {
    "upper body",
    "bust shot",
    "head-and-shoulders framing",
    "portrait",
    "three-quarter view",
}
LOWER_GARMENTS = {
    "skirt",
    "shorts",
    "pants",
    "jeans",
    "trousers",
    "stockings",
    "socks",
    "tights",
    "shoes",
    "boots",
    "heels",
    "loafers",
}


def drop_invisible_clothes(tokens: list[str]) -> list[str]:
    s = {t.lower().strip() for t in tokens}
    # 上半身キューが1つでもあれば下半身タグを落とす
    if s & UPPER_BODY_CUES:
        return [t for t in tokens if t.lower().strip() not in LOWER_GARMENTS]
    return tokens


def drop_contradictions(tags: list[str]) -> list[str]:
    s = set(t.strip().lower() for t in tags)

    # 髪（既存）
    hair = {"long hair", "short hair", "very short hair", "medium hair"}
    if len(s & hair) >= 2:
        s -= hair

    # 目まわり
    eye_pos = {"looking at camera", "eye contact", "open eyes"}
    if (s & eye_pos) and "closed eyes" in s:
        s.remove("closed eyes")

    # 口まわり
    if "smile" in s and "closed mouth" in s:
        s.remove("closed mouth")

    # フレーミング
    if "tight framing" in s and "loose framing" in s:
        hint_tight = {"bust shot", "upper body", "head-and-shoulders framing"}
        if s & hint_tight:
            s.discard("loose framing")
        else:
            s.discard("tight framing")
    # 上半身キューがあるなら loose framing は落とす
    if "loose framing" in s and (s & UPPER_BODY_CUES):
        s.discard("loose framing")

    # 構図
    if "rule of thirds" in s and "centered composition" in s:
        # 迷ったら映える「rule of thirds」を優先
        s.discard("centered composition")
    # balanced と centered が同居したら centered を落とす
    if "balanced composition" in s and "centered composition" in s:
        s.discard("centered composition")

    # フォーカス
    if "sharp focus" in s and "soft focus" in s:
        s.discard("soft focus")

    # 絞り
    if "wide aperture" in s and "narrow aperture" in s:
        if "shallow depth" in s:
            s.discard("narrow aperture")
        else:
            s.discard("wide aperture")

    return [t for t in tags if t.strip().lower() in s]


def adjust_framing_for_cues(tokens: list[str]) -> list[str]:
    s = {t.lower().strip() for t in tokens}
    if s & UPPER_BODY_CUES and "loose framing" in s:
        return [
            "tight framing" if t.lower().strip() == "loose framing" else t
            for t in tokens
        ]
    return tokens


REDUNDANT_GROUPS = [
    {"warm tones", "warm color palette", "muted colors", "neutral palette"},
    {"soft contrast", "low contrast look"},
    {"depth of field", "shallow depth"},
    {"subtle bokeh", "creamy bokeh"},
    {"balanced composition", "negative space balance"},
    {"fine details", "surface detail", "refined detail"},
    {"looking at camera", "eye contact"},
    {"gentle shadow", "subtle shadows", "soft shadows"},
    {"photographic realism", "life-like rendering"},
]

# 追加の冗長グループ
REDUNDANT_GROUPS += [
    {"gentle tonality", "soft tonality"},
    {"realistic texture", "natural rendition", "clean rendition"},
    {"window light", "window light pattern"},
]

PREFER_ORDER = {
    "warm tones": 0,
    "soft contrast": 0,
    "shallow depth": 0,
    "subtle bokeh": 0,
    "balanced composition": 0,
    "fine details": 0,
    "looking at camera": 0,
    "gentle shadow": 0,
    "photographic realism": 0,
}

PREFER_ORDER.update(
    {
        "gentle tonality": 0,
        "realistic texture": 0,
        "window light": 0,
    }
)

# すべてのグループを索引化
_ALL_GROUPS = [set(g) for g in REDUNDANT_GROUPS]
_TERM2GID = {}
for gid, group in enumerate(_ALL_GROUPS):
    for term in group:
        _TERM2GID[term.lower()] = gid

def _would_be_group_dup(term: str, current: list[str]) -> bool:
    """term を入れると同義グループが重複するか？（代表1語ルール）"""
    gid = _TERM2GID.get(term.lower())
    if gid is None:
        return False
    cur = {t.lower() for t in current}
    return any(x in cur for x in _ALL_GROUPS[gid])


def _would_conflict(term: str, current: list[str]) -> bool:
    """候補 term を入れると矛盾や衝突が起きるなら True"""
    t = term.strip().lower()
    cur = {c.strip().lower() for c in current}

    # 構図
    if t == "centered composition" and "balanced composition" in cur:
        return True
    if t == "balanced composition" and "centered composition" in cur:
        return True

    # フレーミング（上半身キューがあるなら loose は避ける）
    if (t == "loose framing") and (cur & UPPER_BODY_CUES):
        return True
    if (t == "tight framing") and ("loose framing" in cur):
        return True

    # フォーカス／絞り
    if t == "soft focus" and "sharp focus" in cur:
        return True
    if t == "sharp focus" and "soft focus" in cur:
        return True
    if t == "narrow aperture" and "shallow depth" in cur:
        return True
    if t == "wide aperture" and "shallow depth" not in cur and "depth of field" in cur:
        return False

    # 目の状態
    if t == "closed eyes" and ({"looking at camera", "eye contact", "open eyes"} & cur):
        return True

    return False


def compress_redundant(tokens: list[str]) -> list[str]:
    s = [t.strip() for t in tokens]
    keep = set(t.lower() for t in s)

    for group in REDUNDANT_GROUPS:
        inter = keep & {g.lower() for g in group}
        if len(inter) >= 2:
            ranked = sorted(inter, key=lambda x: PREFER_ORDER.get(x, 999))
            winner = ranked[0]
            keep -= inter
            keep.add(winner)

    return [t for t in s if t.lower() in keep]


CAPTION_OBJECTS = [
    "table",
    "laptop",
    "phone",
    "camera",
    "microphone",
    "book",
    "cup",
    "glass",
    "bottle",
    "pen",
    "pencil",
    "flower",
    "cat",
    "dog",
    "bag",
    "hat",
    "guitar",
    "headphones",
]


def sync_caption_to_prompt(caption: str, tokens: list[str]) -> str:
    if not caption:
        return caption
    s = {t.lower().strip() for t in tokens}
    text = " " + caption.strip()

    for obj in CAPTION_OBJECTS:
        if obj not in s and re.search(rf"\b{obj}s?\b", text, flags=re.I):
            # with/holding/using/on/at/near/by/sitting at/standing at ... <obj>
            patterns = [
                rf"\s(?:with|holding|using|on|at|near|by)\b[^,\.]*\b{obj}s?\b",
                rf"\s(?:sitting|standing)\s+(?:at|near|by)\b[^,\.]*\b{obj}s?\b",
            ]
            for pat in patterns:
                text = re.sub(pat, "", text, flags=re.I)

    text = re.sub(r"\s{2,}", " ", text).strip(" ,.;")
    return text


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


def merge_unique(*lists: Sequence[str]) -> list[str]:
    out, seen = [], set()
    for ls in lists:
        for w in ls:
            if w not in seen:
                out.append(w)
                seen.add(w)
    return out


# ---- SAFE_FILL pools per style/profile ----
SAFE_FILL_PHOTO_SINGLE_UPPER = SAFE_FILL

SAFE_FILL_PHOTO_FULLBODY = merge_unique(SAFE_FILL, [
    "full body",
    "full-length framing",
    "standing pose",
    "natural stance",
    "balanced posture",
    "head-to-toe composition",
    "silhouette clarity",
    "garment detail",
    "fabric texture",
    "shoe detail",
    "body proportion balance",
    "pose stability",
])

SAFE_FILL_PHOTO_GROUP_UPPER = merge_unique(SAFE_FILL, [
    "group portrait",
    "subject spacing",
    "staggered heights",
    "layered arrangement",
    "even illumination across subjects",
    "consistent white balance",
    "minimal overlap",
    "depth separation for subjects",
])

SAFE_FILL_PHOTO_GROUP_FULL = merge_unique(SAFE_FILL_PHOTO_FULLBODY, [
    "group portrait",
    "subject spacing",
    "staggered heights",
    "layered arrangement",
    "even illumination across subjects",
    "minimal overlap",
    "depth separation for subjects",
])

SAFE_FILL_ANIME_SINGLE_UPPER = [
    # drawing & lines
    "clean line art",
    "consistent outline",
    "crisp edges",
    "line weight control",
    "inked contours",
    # shading & color
    "cel shading",
    "flat shading",
    "soft gradients",
    "minimal banding",
    "simple color palette",
    "color harmony",
    "anime proportions",
    "face lighting",
    "hair highlights",
    "eye highlights",
    "expressive eyes",
    # framing & layout
    "facing viewer",
    "character silhouette",
    "pose clarity",
    "panel-friendly framing",
    "readable shapes",
    # background
    "clean backdrop",
    "simple backdrop",
    "uncluttered backdrop",
    "negative space",
    # finish
    "smooth fill",
    "uniform tones",
    "color separation",
    "edge cleanliness",
    "SFX-ready space",
    "screen-tone friendly",
    "print-safe contrast",
    "soft glow hint",
    "subtle rim light",
    "gentle vignette",
    # stability extras
    "uniform line density",
    "flat color blocks",
    "selective detailing",
    "shape language clarity",
    "visual coherence",
    "design consistency",
    "appeal-focused rendering",
]

SAFE_FILL_ANIME_FULLBODY = merge_unique(SAFE_FILL_ANIME_SINGLE_UPPER, [
    "full body",
    "full-length framing",
    "standing pose",
    "natural stance",
    "silhouette readability",
    "garment folds",
    "fabric rendering",
    "shoe design",
    "proportion consistency",
    "gesture clarity",
])

SAFE_FILL_ANIME_GROUP_UPPER = merge_unique(SAFE_FILL_ANIME_SINGLE_UPPER, [
    "group composition",
    "subject spacing",
    "staggered heights",
    "overlap control",
    "face readability",
    "consistent outlines across subjects",
])

SAFE_FILL_ANIME_GROUP_FULL = merge_unique(SAFE_FILL_ANIME_FULLBODY, [
    "group composition",
    "subject spacing",
    "staggered heights",
    "overlap control",
    "silhouette separation",
    "ensemble balance",
])
CONTRA_FILL = {
    "soft focus": {"sharp focus"},
    "sharp focus": {"soft focus"},
    "wide aperture": {"narrow aperture"},
    "narrow aperture": {"wide aperture"},
    "tight framing": {"loose framing"},
    "loose framing": {"tight framing"},
    "centered composition": {"rule of thirds"},
    "rule of thirds": {"centered composition"},
}


def finalize_prompt_safe(
    tokens: list[str],
    min_tokens=55,
    max_tokens=65,
    context=None,
) -> list[str]:
    out = tokens[:]

    # 1) 先に圧縮して冗長を削る
    out = compress_redundant(out)

    # 2) 補充（同義グループの重複は追加しない）
    if len(out) < min_tokens:
        rnd = random.Random(_seed_from_context(context or out))
        pool = SAFE_FILL[:]
        rnd.shuffle(pool)
        seen = set(out)
        bg_present = any("background" in t or "backdrop" in t for t in out)
        for w in pool:
            if len(out) >= min_tokens:
                break
            if w in seen:
                continue
            if "background" in w or "backdrop" in w:
                if bg_present:
                    continue
                w = "clean background"
            if any(c in seen for c in CONTRA_FILL.get(w, set())):
                continue
            if _would_be_group_dup(w, out):
                continue
            if _would_conflict(w, out):
                continue
            out.append(w)
            seen.add(w)
            if "background" in w or "backdrop" in w:
                bg_present = True

    # 3) 念のためもう一度だけ圧縮
    out = compress_redundant(out)

    # 4) 上限で切り詰め
    if len(out) > max_tokens:
        out = out[:max_tokens]
    return out


def finalize_pipeline(
    tokens: list[str],
    caption: str | None = None,
    wd14_tags: Iterable[str] | None = None,
    ci_picks: Sequence[str] | None = None,
    style: str = "auto",
    profile: str = "auto",
    blocked_names: set[str] | None = None,
):
    tokens = normalize_terms(tokens)
    tokens = dedupe_background(tokens)
    st, pf, tokens, caption, flags = run_pipeline(
        tokens=tokens,
        caption=caption,
        wd14_tags=wd14_tags,
        ci_picks=ci_picks,
        style=style,
        profile=profile,
        blocked_names=blocked_names,
    )
    return st, pf, tokens, caption, flags


# =========================
# Style / Profile Router
# =========================

ANIME_HINTS = {
    "anime",
    "manga",
    "2d",
    "illustration",
    "lineart",
    "cel shading",
    "flat shading",
    "chibi",
    "cartoon",
    "toon",
    "koukyou shihen",
    "waifu",
    "vtuber",
    "pixiv",
    "doujin",
}


def choose_style(wd14_tags: Iterable[str], caption: str, prefer: str = "auto") -> str:
    st = (prefer or "auto").lower()
    if st in ("photo", "anime"):
        return st
    s = {t.lower().strip() for t in (wd14_tags or [])}
    cap = (caption or "").lower()
    if (s & ANIME_HINTS) or any(k in cap for k in ANIME_HINTS):
        return "anime"
    return "photo"


def select_profile(wd14_tags: Iterable[str], caption: str) -> str:
    s = {t.lower().strip() for t in (wd14_tags or [])}
    cap = (caption or "").lower()
    multi = any(
        k in s or k in cap
        for k in [
            "2girls",
            "2boys",
            "3girls",
            "3boys",
            "group",
            "crowd",
            "several people",
            "a group of",
            "multiple people",
        ]
    )
    full = any(
        k in s or k in cap
        for k in [
            "full body",
            "full-body",
            "full length",
            "full-length",
            "head to toe",
            "head-to-toe",
            "standing full length",
        ]
    )
    if not multi and not full:
        return "single_upper"
    if not multi and full:
        return "single_fullbody"
    if multi and not full:
        return "group_upper"
    return "group_fullbody"


PROFILES = {
    "single_upper": {
        "allow_lower_garments": False,
        "unify_background": True,
        "framing_k": 2,
        "enforce_eye_contact": True,
        "hair_rules": "strict",
    },
    "single_fullbody": {
        "allow_lower_garments": True,
        "unify_background": True,
        "framing_k": 2,
        "enforce_eye_contact": True,
        "hair_rules": "lenient",
    },
    "group_upper": {
        "allow_lower_garments": False,
        "unify_background": False,
        "framing_k": 1,
        "enforce_eye_contact": False,
        "hair_rules": "neutral",
    },
    "group_fullbody": {
        "allow_lower_garments": True,
        "unify_background": False,
        "framing_k": 1,
        "enforce_eye_contact": False,
        "hair_rules": "neutral",
    },
}


def unify_background_style(tokens: list[str], style: str, enable: bool) -> list[str]:
    if not enable:
        return tokens
    tgt = "clean backdrop" if style == "anime" else "clean background"
    groups = [
        {
            "clean background",
            "simple background",
            "uncluttered background",
            "plain background",
            "soft backdrop",
            "simple backdrop",
            "clean backdrop",
        },
    ]
    keep = set(t.lower().strip() for t in tokens)
    for g in groups:
        if keep & g:
            keep -= g
            keep.add(tgt)
    return [t for t in tokens if t.lower().strip() in keep]


def drop_contradictions_style(tags: list[str], style: str = "photo") -> list[str]:
    s = set(t.strip().lower() for t in tags)

    hair = {"long hair", "short hair", "very short hair", "medium hair"}
    if len(s & hair) >= 2:
        s -= hair

    eye_pos = {"looking at camera", "eye contact", "open eyes", "facing viewer"}
    if (s & eye_pos) and "closed eyes" in s:
        s.remove("closed eyes")

    if "smile" in s and "closed mouth" in s:
        s.remove("closed mouth")

    if "tight framing" in s and "loose framing" in s:
        s.discard("loose framing")
    if "rule of thirds" in s and "centered composition" in s:
        s.discard("centered composition")
    if "balanced composition" in s and "centered composition" in s:
        s.discard("centered composition")
    if "loose framing" in s and (s & UPPER_BODY_CUES):
        s.discard("loose framing")

    if style == "photo":
        if "sharp focus" in s and "soft focus" in s:
            s.discard("soft focus")
        if "wide aperture" in s and "narrow aperture" in s:
            if "shallow depth" in s:
                s.discard("narrow aperture")
            else:
                s.discard("wide aperture")

    if style == "anime":
        if "cel shading" in s and "painterly shading" in s:
            s.discard("painterly shading")
        if "flat shading" in s and "realistic texture" in s:
            s.discard("realistic texture")
        if "thick outline" in s and "no outline" in s:
            s.discard("no outline")
        for ban in (
            "bokeh",
            "depth of field",
            "wide aperture",
            "narrow aperture",
            "photographic realism",
        ):
            if ban in s:
                s.discard(ban)

    return [t for t in tags if t.strip().lower() in s]


FRAMING_ORDER = [
    "portrait",
    "upper body",
    "head-and-shoulders framing",
    "bust shot",
    "three-quarter view",
    "full body",
    "full-length framing",
]
FRAMING_SET = {t.lower() for t in FRAMING_ORDER}


def compress_framing(tokens: list[str], k: int = 2) -> list[str]:
    keep, others, seen = [], [], set()
    for t in tokens:
        tl = t.strip().lower()
        if tl in FRAMING_SET and tl not in seen:
            keep.append(tl)
            seen.add(tl)
        else:
            others.append(t)
    keep = sorted(keep, key=lambda x: FRAMING_ORDER.index(x))[:k]
    return [t for t in others] + keep


def _seed_from_context(context: Sequence[str] | None = None) -> int:
    if not context:
        return 123456789
    h = hashlib.sha1(("||".join(map(str, context))).encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def finalize_prompt_safe_ext(
    tokens: list[str],
    min_tokens: int = 55,
    max_tokens: int = 65,
    context: Sequence[str] | None = None,
    safe_pool: Sequence[str] | None = None,
) -> list[str]:
    out = compress_redundant(tokens[:])
    pool = list(safe_pool or SAFE_FILL)
    if len(out) < min_tokens and pool:
        rnd = random.Random(_seed_from_context(context or out))
        rnd.shuffle(pool)
        cur = set(out)
        for w in pool:
            if len(out) >= min_tokens:
                break
            if w in cur:
                continue
            if any(c in cur for c in CONTRA_FILL.get(w, set())):
                continue
            out.append(w)
            cur.add(w)
    out = compress_redundant(out)
    if len(out) < min_tokens and pool:
        for w in pool:
            if len(out) >= min_tokens:
                break
            if w in out:
                continue
            if any(c in out for c in CONTRA_FILL.get(w, set())):
                continue
            out.append(w)
    return out[:max_tokens]


def _choose_safe_pool(style: str, profile: str) -> list[str]:
    if style == "photo":
        if profile == "single_upper":
            return SAFE_FILL_PHOTO_SINGLE_UPPER
        if profile == "single_fullbody":
            return SAFE_FILL_PHOTO_FULLBODY
        if profile == "group_upper":
            return SAFE_FILL_PHOTO_GROUP_UPPER
        if profile == "group_fullbody":
            return SAFE_FILL_PHOTO_GROUP_FULL
    else:
        if profile == "single_upper":
            return SAFE_FILL_ANIME_SINGLE_UPPER
        if profile == "single_fullbody":
            return SAFE_FILL_ANIME_FULLBODY
        if profile == "group_upper":
            return SAFE_FILL_ANIME_GROUP_UPPER
        if profile == "group_fullbody":
            return SAFE_FILL_ANIME_GROUP_FULL
    return SAFE_FILL


def run_pipeline(
    tokens: list[str],
    caption: str | None,
    wd14_tags: Iterable[str] | None,
    ci_picks: Sequence[str] | None = None,
    style: str = "auto",
    profile: str = "auto",
    blocked_names: set[str] | None = None,
):
    st = choose_style(wd14_tags or [], caption or "", prefer=style)
    pf = profile if profile in PROFILES else select_profile(wd14_tags or [], caption or "")
    cfg = PROFILES[pf]
    pool = _choose_safe_pool(st, pf)

    t = tokens[:]

    t = unify_background_style(t, st, enable=bool(cfg["unify_background"]))
    if st == "photo" and not cfg["allow_lower_garments"]:
        t = drop_invisible_clothes(t)
    t = drop_contradictions_style(t, style=st)
    t = purge_artist_fragments(t, blocked_fullnames=blocked_names)
    t = compress_framing(t, k=int(cfg["framing_k"]))

    t = finalize_prompt_safe_ext(
        t,
        min_tokens=55,
        max_tokens=65,
        context=ci_picks or t,
        safe_pool=pool,
    )

    t = drop_contradictions_style(t, style=st)
    t = compress_redundant(t)
    t = unify_background_style(t, st, enable=bool(cfg["unify_background"]))
    if len(t) < 55:
        t = finalize_prompt_safe_ext(
            t,
            min_tokens=55,
            max_tokens=65,
            context=ci_picks or t,
            safe_pool=pool,
        )
        t = unify_background_style(t, st, enable=bool(cfg["unify_background"]))
        if len(t) < 55:
            t = finalize_prompt_safe_ext(
                t,
                min_tokens=55,
                max_tokens=65,
                context=ci_picks or t,
                safe_pool=pool,
            )
    t = dedupe_background(t)
    if len(t) < 55:
        t = finalize_prompt_safe_ext(
            t,
            min_tokens=55,
            max_tokens=65,
            context=ci_picks or t,
            safe_pool=pool,
        )
        t = unify_background_style(t, st, enable=bool(cfg["unify_background"]))
        t = dedupe_background(t)

    try:
        new_cap = sync_caption_to_prompt(caption or "", t)
    except NameError:
        new_cap = caption or ""

    flags = {
        "style": st,
        "profile": pf,
        "unify_bg": bool(cfg["unify_background"]),
        "allow_lower_garments": bool(cfg["allow_lower_garments"]),
        "framing_k": int(cfg["framing_k"]),
        "hair": cfg["hair_rules"],
    }

    return st, pf, t, new_cap, flags

