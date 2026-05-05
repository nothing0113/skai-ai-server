from __future__ import annotations

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


def grade_answer(
    model_store: ModelStore,
    reference_answer: str,
    user_answer: str,
    keywords: list[str],
) -> dict:
    dense01 = model_store.dense.similarity(reference_answer, user_answer)
    sparse01 = model_store.sparse.similarity(reference_answer, user_answer)
    keyword01, missing = keyword_score(user_answer, keywords)

    dense = dense01 * 100.0
    sparse = sparse01 * 100.0
    keyword = keyword01 * 100.0
    final_score = dense * 0.45 + sparse * 0.30 + keyword * 0.25

    return {
        "denseScore": round(dense, 1),
        "sparseScore": round(sparse, 1),
        "keywordScore": round(keyword, 1),
        "finalScore": round(final_score, 1),
        "missingKeywords": missing,
        "weakConcepts": missing,
    }
