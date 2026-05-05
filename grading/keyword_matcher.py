from __future__ import annotations

import re


SYNONYMS = {
    "ai": {"artificialintelligence", "인공지능"},
    "llm": {"large language model", "거대언어모델"},
    "cpu": {"processor", "중앙처리장치"},
}


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9가-힣\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def expand_keyword(keyword: str) -> set[str]:
    base = normalize_text(keyword)
    expanded = {base}
    expanded.update(SYNONYMS.get(base, set()))
    return {normalize_text(k) for k in expanded if k}


def keyword_score(answer: str, keywords: list[str]) -> tuple[float, list[str]]:
    normalized_answer = normalize_text(answer)
    missing: list[str] = []
    hit = 0
    for kw in keywords:
        forms = expand_keyword(kw)
        if any(form and form in normalized_answer for form in forms):
            hit += 1
        else:
            missing.append(kw)
    if not keywords:
        return 0.0, []
    return hit / len(keywords), missing
