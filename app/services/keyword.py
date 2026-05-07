from __future__ import annotations

import re
from typing import Iterable

STOPWORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "of",
    "to",
    "and",
    "or",
    "for",
    "이",
    "그",
    "저",
    "은",
    "는",
    "이다",
    "하다",
}

GLOBAL_CANDIDATE_BANK: dict[str, set[str]] = {
    "인공지능": {"ai", "artificial intelligence", "머신러닝", "기계학습"},
    "거대언어모델": {"llm", "large language model", "생성형ai", "생성형 ai"},
    "중앙처리장치": {"cpu", "processor"},
    "그래픽처리장치": {"gpu", "graphics processing unit"},
}

SURFACE_SYNONYMS: dict[str, set[str]] = {
    "ai": {"인공지능", "artificial intelligence"},
    "llm": {"거대언어모델", "large language model"},
    "cpu": {"중앙처리장치", "processor"},
}

PAREN_RE = re.compile(r"\(([^)]*)\)")


def normalize_text(text: str, collapse_for_contains: bool = False) -> str:
    normalized = text.lower().strip()
    normalized = re.sub(r"[^a-z0-9가-힣\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if collapse_for_contains:
        return normalized.replace(" ", "")
    return normalized


def _strip_stopwords(text: str) -> str:
    tokens = [tok for tok in normalize_text(text).split() if tok and tok not in STOPWORDS]
    return " ".join(tokens)


def _parenthetical_variants(keyword: str) -> set[str]:
    variants = {keyword}
    paren = PAREN_RE.findall(keyword)
    if paren:
        variants.update(paren)
        no_paren = PAREN_RE.sub(" ", keyword)
        variants.add(no_paren)
    return {v.strip() for v in variants if v.strip()}


def _surface_expand(keyword: str) -> set[str]:
    expanded = {keyword}
    base = normalize_text(keyword)
    expanded.update(SURFACE_SYNONYMS.get(base, set()))
    return expanded


def _bank_expand(keyword: str) -> set[str]:
    key = normalize_text(keyword)
    expanded = {keyword}
    for canon, candidates in GLOBAL_CANDIDATE_BANK.items():
        normalized_candidates = {normalize_text(c) for c in candidates}
        if key == normalize_text(canon) or key in normalized_candidates:
            expanded.add(canon)
            expanded.update(candidates)
    return expanded


def expand_keyword(keyword: str) -> set[str]:
    forms: set[str] = set()
    for variant in _parenthetical_variants(keyword):
        for surfaced in _surface_expand(variant):
            forms.add(normalize_text(surfaced))
            forms.add(_strip_stopwords(surfaced))
            for banked in _bank_expand(surfaced):
                forms.add(normalize_text(banked))
                forms.add(_strip_stopwords(banked))
    return {f for f in forms if f}


def _best_form_hit(answer_collapsed: str, forms: Iterable[str]) -> bool:
    for form in forms:
        collapsed_form = normalize_text(form, collapse_for_contains=True)
        if collapsed_form and collapsed_form in answer_collapsed:
            return True
    return False


def keyword_match(answer: str, keywords: list[str]) -> tuple[float, list[str], list[str]]:
    if not keywords:
        return 0.0, [], []

    normalized_answer = normalize_text(answer)
    answer_collapsed = normalize_text(normalized_answer, collapse_for_contains=True)

    missing: list[str] = []
    matched: list[str] = []
    hits = 0

    for keyword in keywords:
        forms = expand_keyword(keyword)
        if _best_form_hit(answer_collapsed, forms):
            hits += 1
            matched.append(keyword)
        else:
            missing.append(keyword)

    return hits / len(keywords), matched, missing
