import re
NAME_PAT = re.compile(r"\b[a-z][a-z]+ [a-z][a-z]+\b", re.I)
NUMERIC_PAT = re.compile(r"^\d+$")

# 明示NG語（厳格一致）…必要最小限だけ
BAD_TOKENS_EXACT = {
    "ayami kojima","tsugumi ohba","kohei murata","ayami","kojima","ohba","murata"
}

def clean_tokens(tokens):
    out, seen = [], set()
    for t in tokens:
        t = (t or "").strip(" ,.;:").lower()
        if not (2 <= len(t) <= 40):   continue
        if NAME_PAT.search(t):        continue
        if t in BAD_TOKENS_EXACT:     continue  # ← 部分一致はやめる
        if NUMERIC_PAT.match(t):      continue
        if t not in seen:
            seen.add(t); out.append(t)
    return out
