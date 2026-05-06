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


def _token_forms(text: str) -> set[str]:
    parts = re.findall(r"[a-z0-9가-힣]+", normalize_text(text))
    return {p for p in parts if p}


def expand_keyword(keyword: str) -> set[str]:
    base = normalize_text(keyword)
    expanded = {base}
    expanded.update(SYNONYMS.get(base, set()))
    forms = {normalize_text(k) for k in expanded if k}
    for item in list(forms):
        forms.update(_token_forms(item))
    return {f for f in forms if f}


def _extract_parenthesis_aliases(reference_answer: str) -> dict[str, set[str]]:
    groups: dict[str, set[str]] = {}
    for left, alias in re.findall(r"([가-힣a-zA-Z0-9\s]+)\(([^)]+)\)", reference_answer):
        left_forms = _token_forms(left)
        alias_forms = _token_forms(alias)
        merged = left_forms | alias_forms
        if not merged:
            continue
        for form in merged:
            groups.setdefault(form, set()).update(merged)
    return groups


def keyword_score(
    answer: str,
    keywords: list[str],
    reference_answer: str = "",
) -> tuple[float, list[str]]:
    normalized_answer = normalize_text(answer)
    alias_groups = _extract_parenthesis_aliases(reference_answer) if reference_answer else {}
    missing: list[str] = []
    hit = 0
    for kw in keywords:
        forms = expand_keyword(kw)
        for form in list(forms):
            forms.update(alias_groups.get(form, set()))
        if any(form and form in normalized_answer for form in forms):
            hit += 1
        else:
            missing.append(kw)
    if not keywords:
        return 0.0, []
    return hit / len(keywords), missing
