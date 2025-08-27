import re

NAME_PAT = re.compile(r"\b[a-z][a-z]+ [a-z][a-z]+\b", re.I)
NUMERIC_PAT = re.compile(r"^\d+$")
BAD_TOKENS = {"ayami", "kojima", "tsugumi", "ohba", "murata", "kohei"}


def clean_tokens(tokens):
    out = []
    for t in tokens:
        t = t.strip(", ").lower()
        if not t or len(t) < 2 or len(t) > 40:
            continue
        if NAME_PAT.search(t):
            continue
        if NUMERIC_PAT.match(t):
            continue
        if any(bt in t for bt in BAD_TOKENS):
            continue
        out.append(t)
    seen = set()
    dedup = []
    for t in out:
        if t not in seen:
            seen.add(t)
            dedup.append(t)
    return dedup

