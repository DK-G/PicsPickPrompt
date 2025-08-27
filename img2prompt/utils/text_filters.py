import re

NAME_PAT = re.compile(r"\b[a-z][a-z]+ [a-z][a-z]+\b", re.I)  # 英字2語の姓名
BAD_TOKENS = {"ayami", "kojima", "tsugumi", "ohba", "murata", "kohei"}


def strip_names(tokens):
    out = []
    for t in tokens:
        t = t.strip(", ").lower()
        if not t:
            continue
        if NAME_PAT.search(t):  # 2語姓名を除外
            continue
        if any(bt in t for bt in BAD_TOKENS):  # 明示NG語
            continue
        out.append(t)
    return out
