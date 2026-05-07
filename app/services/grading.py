from __future__ import annotations

import math

from app.schemas import Evidence, ScoreSet
from app.services.keyword import keyword_match, normalize_text


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0

    score = dot / (na * nb)
    return max(0.0, min(1.0, score))


def normalize_score(sim: float, low: float, high: float) -> float:
    if sim <= low:
        return 0.0
    if sim >= high:
        return 1.0
    return (sim - low) / (high - low)


def dense_to_score(sim: float) -> float:
    return normalize_score(sim, low=0.45, high=0.85) * 100.0


def sparse_to_score(sim: float) -> float:
    return normalize_score(sim, low=0.05, high=0.45) * 100.0


def grade_answer(
    model_answer: str,
    student_answer: str,
    keywords: list[str],
    dense_vectors: list[list[float]],
    sparse_similarity: float,
) -> tuple[ScoreSet, Evidence]:
    dense_sim = cosine_similarity(dense_vectors[0], dense_vectors[1])
    keyword01, matched, _ = keyword_match(student_answer, keywords)

    dense = round(dense_to_score(dense_sim), 1)
    sparse = round(sparse_to_score(sparse_similarity), 1)
    keyword = round(keyword01 * 100.0, 1)
    total = round((dense * 0.45) + (sparse * 0.30) + (keyword * 0.25), 1)

    scores = ScoreSet(
        denseScore=dense,
        sparseScore=sparse,
        keywordScore=keyword,
        totalScore=total,
    )
    evidence = Evidence(
        matchedKeywords=matched,
        normalizedStudentAnswer=normalize_text(student_answer),
        normalizedModelAnswer=normalize_text(model_answer),
    )
    return scores, evidence
