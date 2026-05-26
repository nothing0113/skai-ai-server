from __future__ import annotations

import re
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from app.schemas import KeywordWithVariants

STOPWORDS = {
    "the", "a", "an", "is", "are", "of", "to", "and", "or", "for",
    "이", "그", "저", "은", "는", "이다", "하다", "있다", "없다",
    "것", "수", "등", "및", "위해", "통해", "위한", "대한",
    "방식", "방법", "형태", "구조", "과정", "결과", "경우",
    "스스", "한다", "된다", "있다", "없다", "해야", "하여", "하며",
    "찾아낸다", "사용한다", "이용한다", "필요하다", "가능하다",
    "직접", "자동", "기반", "입력", "출력", "전통적인", "일반적인",
}

GLOBAL_CANDIDATE_BANK: dict[str, set[str]] = {
    # AI / 인공지능
    "인공지능": {"ai", "artificial intelligence", "머신러닝", "기계학습", "딥러닝", "deep learning"},
    # 학습 계열
    "학습": {"머신러닝", "기계학습", "machine learning", "딥러닝", "deep learning",
             "훈련", "training", "학습하다", "배우다", "학습과정"},
    # 추론 계열
    "추론": {"판단", "reasoning", "inference", "예측", "prediction", "판단하다",
             "결론", "도출", "분류", "생각하다", "인식"},
    # 문제 해결
    "문제해결": {"문제 해결", "problem solving", "솔루션", "solution"},
    # LLM
    "거대언어모델": {"llm", "large language model", "생성형ai", "생성형 ai"},
    # 하드웨어
    "중앙처리장치": {"cpu", "processor"},
    "그래픽처리장치": {"gpu", "graphics processing unit"},
    # 알고리즘
    "알고리즘": {"algorithm", "로직", "logic", "절차", "방법론"},
    # 데이터
    "데이터": {"data", "데이터셋", "dataset", "정보"},
    # 신경망
    "신경망": {"neural network", "뉴럴넷", "뉴럴네트워크", "딥러닝", "deep learning"},
    # 자연어처리
    "자연어처리": {"nlp", "natural language processing", "텍스트 분석", "언어모델"},
}

SURFACE_SYNONYMS: dict[str, set[str]] = {
    "ai": {"인공지능", "artificial intelligence"},
    "llm": {"거대언어모델", "large language model"},
    "cpu": {"중앙처리장치", "processor"},
    "gpu": {"그래픽처리장치", "graphics processing unit"},
    "ml": {"머신러닝", "기계학습", "machine learning"},
    "nlp": {"자연어처리", "natural language processing"},
    "머신러닝": {"학습", "기계학습", "machine learning"},
    "딥러닝": {"학습", "신경망", "deep learning"},
    "판단": {"추론", "reasoning", "inference"},
    "예측": {"추론", "inference", "prediction"},
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


def keyword_match(answer: str, keywords: "list[KeywordWithVariants]", sparse: "SparseService | None" = None) -> tuple[float, list[str], list[str]]:
    if not keywords:
        return 0.0, [], []

    normalized_answer = normalize_text(answer)
    answer_collapsed = normalize_text(normalized_answer, collapse_for_contains=True)

    missing: list[str] = []
    matched: list[str] = []
    hits = 0

    for kw in keywords:
        # term + variants 모두 확장해서 매칭
        all_forms: set[str] = set()
        for candidate in [kw.term] + kw.variants:
            all_forms.update(expand_keyword(candidate))

        if _best_form_hit(answer_collapsed, all_forms):
            hits += 1
            matched.append(kw.term)
        else:
            missing.append(kw.term)

    return hits / len(keywords), matched, missing
