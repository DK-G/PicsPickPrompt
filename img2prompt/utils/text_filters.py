import re
import unicodedata

# TitleCase の姓名だけを人名とみなす（写真語 "upper body" 等を誤排除しない）
NAME_TITLECASE = re.compile(r"\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b")

NUMERIC_PAT = re.compile(r"^\d+$")

# 既知のアーティスト名（最小限）
ARTIST_TOKENS = {
    "Ayami Kojima","Rei Hiroe","Shiori Teshirogi","Tsugumi Ohba",
    "Tsukasa Dokite","Omina Tachibana","Kohei Murata",
    "Ayami","Kojima","Ohba","Murata","Teshirogi","Hiroe",
}

# 線画/アニメ系の“除外候補”（サブストリングOK）
BAN_SUBSTR = {
    "1girl","1boy","solo","comic","manga","cartoon","lineart","sketch",
    "monochrome","grayscale","greyscale","sensitive"
}

# 写真系の“二語フレーズ”は明示ホワイトリストで必ず通す
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
    # 空白を詰めた比較で OCR 崩れにも耐性
    raw_nfkc = unicodedata.normalize("NFKC", raw).strip()
    nospace = raw_nfkc.replace(" ", "")
    for a in ARTIST_TOKENS:
        if raw_nfkc == a or nospace == a.replace(" ", ""):
            return True
    # TitleCase 姓名のみ人名判定（lower化後の二語は弾かない）
    return NAME_TITLECASE.search(raw) is not None

def clean_tokens(tokens):
    out, seen = [], set()
    for raw in tokens:
        if not raw: 
            continue
        # ホワイトリスト先行：写真系二語は無条件で通す
        if _nfkc_lower(raw) in SAFE_TWO_WORDS:
            t = _nfkc_lower(raw)
            if t not in seen:
                seen.add(t); out.append(t)
            continue

        # 通常チェック
        if _is_artist_like(raw):              # 人名/作家名（TitleCase）除外
            continue
        t = _nfkc_lower(raw)
        if not (2 <= len(t) <= 40):           # 極端に短長は除外
            continue
        if NUMERIC_PAT.match(t):              # 純数値は除外
            continue
        if any(b in t for b in BAN_SUBSTR):   # 線画/アニメ系ノイズ
            continue

        if t not in seen:
            seen.add(t); out.append(t)
    return out
