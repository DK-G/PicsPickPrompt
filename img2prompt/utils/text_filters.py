import re
import unicodedata

# OCRで空白が割れた例: "koj ima" もヒットさせる
NAME_TWO_WORDS = re.compile(r"\b[a-z]{2,}\s+[a-z]{2,}\b", re.I)
NUMERIC_PAT = re.compile(r"^\d+$")

# アーティスト系の代表語（必要最小限）──厳格一致と「空白を詰めた一致」の両方で弾く
ARTIST_TOKENS = {
    "ayami kojima","rei hiroe","shiori teshirogi","tsugumi ohba","tsukasa dokite",
    "omina tachibana","kohei murata","ayami","kojima","ohba","murata","teshirogi","hiroe",
}

def _squash_spaces(s: str) -> str:
    # 連続空白を1つに、さらに空白削除版も返す
    s_norm = " ".join(s.split())
    return s_norm, s_norm.replace(" ", "")

def _normalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    return s.strip(" ,.;:").lower()

def is_artist_like(tok: str) -> bool:
    t = _normalize(tok)
    t_space, t_nospace = _squash_spaces(t)
    # 厳格一致
    if t_space in ARTIST_TOKENS or t in ARTIST_TOKENS:
        return True
    # "koj ima" → "kojima" のような分割空白も落とす
    for a in ARTIST_TOKENS:
        a_space, a_nospace = _squash_spaces(a)
        if t_nospace == a_nospace:
            return True
    # 2語の姓名パターンは原則除外（例外を許したければここでホワイトリスト）
    if NAME_TWO_WORDS.search(t):
        return True
    return False

# アニメ/線画系・数え上げタグなどを落とす（サブストリングでOK）
BAN_SUBSTR = {
    "1girl","1boy","solo","comic","manga","cartoon","lineart","sketch","monochrome",
    "grayscale","greyscale","sensitive","dated","general",
}

def is_banned_semantics(tok: str) -> bool:
    t = _normalize(tok)
    return any(b in t for b in BAN_SUBSTR)

def clean_tokens(tokens):
    out, seen = [], set()
    for raw in tokens:
        t = _normalize(raw)
        if not (2 <= len(t) <= 40):  # 極端に短い/長い
            continue
        if NUMERIC_PAT.match(t):     # 純数値
            continue
        if is_artist_like(t):        # 人名/作家名/OCR崩れ
            continue
        if is_banned_semantics(t):   # アニメ/線画/列挙ノイズ
            continue
        if t not in seen:
            seen.add(t); out.append(t)
    return out
