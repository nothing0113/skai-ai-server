from __future__ import annotations

import re

from grading.keyword_matcher import keyword_score
from grading.models import ModelStore


def level_from_score(score: float) -> str:
    if score >= 85:
        return "매우 높음"
    if score >= 70:
        return "높음"
    if score >= 50:
        return "보통"
    return "낮음"


def quality_from_score(score: float) -> int:
    if score >= 80:
        return 5
    if score >= 60:
        return 3
    if score >= 40:
        return 2
    return 0


def _split_concepts(text: str) -> list[str]:
    if not text.strip():
        return []
    normalized = re.sub(r"[;\n]+", ".", text)
    normalized = re.sub(r"\s+(그리고|및|and)\s+", ". ", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"(하고|이며|이고)\s+", ". ", normalized)
    parts = [p.strip(" .") for p in re.split(r"[.!?]", normalized) if p.strip(" .")]
    return parts if parts else [text.strip()]


def _split_sentences(text: str) -> list[str]:
    parts = [p.strip(" .") for p in re.split(r"[.!?\n]", text) if p.strip(" .")]
    return parts if parts else [text.strip()]


def _length_penalty(answer: str) -> float:
    tokens = re.findall(r"[a-z0-9가-힣]+", answer.lower())
    n = len(tokens)
    if n <= 2:
        return 0.7
    if n <= 4:
        return 0.95
    return 1.0


def _token_overlap(a: str, b: str) -> float:
    def norm_tokens(text: str) -> list[str]:
        lowered = text.lower()
        lowered = re.sub(r"([a-z0-9])([가-힣])", r"\1 \2", lowered)
        lowered = re.sub(r"([가-힣])([a-z0-9])", r"\1 \2", lowered)
        raw = re.findall(r"[a-z0-9가-힣]+", lowered)
        particles = {"은", "는", "이", "가", "을", "를", "와", "과", "도", "에", "의"}
        return [t for t in raw if t and t not in particles]

    ta = set(norm_tokens(a))
    tb = set(norm_tokens(b))
    if not ta or not tb:
        return 0.0
    matched = 0
    for tok in ta:
        if tok in tb:
            matched += 1
            continue
        if any((tok in other or other in tok) and min(len(tok), len(other)) >= 2 for other in tb):
            matched += 1
    return matched / len(ta)


def grade_answer(
    model_store: ModelStore,
    reference_answer: str,
    user_answer: str,
    keywords: list[str],
) -> dict:
    dense01 = model_store.dense.similarity(reference_answer, user_answer)
    sparse01 = model_store.sparse.similarity(reference_answer, user_answer)
    keyword01, missing = keyword_score(user_answer, keywords, reference_answer=reference_answer)

    concepts = _split_concepts(reference_answer)
    user_sentences = _split_sentences(user_answer)
    concept_scores: list[tuple[str, float]] = []
    if not user_sentences:
        user_sentences = [""]

    for concept in concepts:
        best = 0.0
        for sent in user_sentences:
            c_dense = model_store.dense.similarity(concept, sent)
            c_sparse = model_store.sparse.similarity(concept, sent)
            c_kw, _ = keyword_score(sent, [concept], reference_answer=reference_answer)
            c_overlap = _token_overlap(concept, sent)
            combined = c_dense * 0.30 + c_sparse * 0.20 + c_kw * 0.20 + c_overlap * 0.30
            if combined > best:
                best = combined
        concept_scores.append((concept, best))

    dense = dense01 * 100.0
    sparse = sparse01 * 100.0
    keyword = keyword01 * 100.0
    base_score = dense * 0.45 + sparse * 0.30 + keyword * 0.25

    if concept_scores:
        concept_avg = sum(s for _, s in concept_scores) / len(concept_scores)
        concept_hit = sum(1 for _, s in concept_scores if s >= 0.35) / len(concept_scores)
        concept_component = (concept_hit * 100.0) * 0.7 + (concept_avg * 100.0) * 0.3
        base_score = base_score * 0.3 + concept_component * 0.7

    final_score = base_score * _length_penalty(user_answer)
    if (dense01 + sparse01) / 2.0 < 0.2:
        final_score = min(final_score, 35.0)
    final_score = max(0.0, min(100.0, final_score))

    weak_concepts = [c for c, s in concept_scores if s < 0.55]
    if not weak_concepts:
        weak_concepts = missing

    return {
        "denseScore": round(dense, 1),
        "sparseScore": round(sparse, 1),
        "keywordScore": round(keyword, 1),
        "finalScore": round(final_score, 1),
        "missingKeywords": missing,
        "weakConcepts": weak_concepts,
    }
