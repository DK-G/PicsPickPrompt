STYLE_PRESETS = {
  "cinematic": ["cinematic feel","soft lighting","bokeh","film grain","high dynamic range"],
  "studio":    ["studio light","sharp focus","clean background","high detail"],
  "natural":   ["natural light","warm tones","realistic texture","subtle shadows"],
  "anime":     ["anime style","clean line","flat shading","vivid colors","cel shading"],
}


def apply_style(prompt_tags: list[str], style: str) -> list[str]:
    extra = STYLE_PRESETS.get(style.lower())
    if not extra:
        return prompt_tags
    seen = set(prompt_tags)
    out = prompt_tags[:]
    for w in extra:
        if w not in seen:
            out.append(w)
            seen.add(w)
    return out
