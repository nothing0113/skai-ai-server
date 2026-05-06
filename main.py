from __future__ import annotations

from contextlib import asynccontextmanager
import json

from fastapi import FastAPI

from config import get_settings
from grading.hybrid_grader import grade_answer, level_from_score
from grading.models import ModelStore
from llm.factory import build_provider
from prompts.feedback_prompt import FEEDBACK_SYSTEM_PROMPT, build_feedback_user_prompt
from prompts.outline_prompt import OUTLINE_SYSTEM_PROMPT, build_outline_user_prompt
from prompts.question_prompt import QUESTION_SYSTEM_PROMPT, build_question_user_prompt
from prompts.review_prompt import REVIEW_SYSTEM_PROMPT, build_review_user_prompt
from prompts.tutor_prompt import OUTLINE_CHAT_SYSTEM_PROMPT, build_tutor_user_prompt
from scheduler.sm2 import apply_sm2, next_review_date
from schemas.evaluation import EvaluateRequest
from schemas.outline import OutlineRequest
from schemas.question import QuestionsRequest
from schemas.review import ReviewContentRequest, ReviewScheduleRequest
from schemas.tutor import ChatRequest
from utils.json_parser import JsonParseError, parse_json_object, retry_message

settings = get_settings()
provider = build_provider(settings)
model_store: ModelStore | None = None

PARSE_FAIL = {
    "success": False,
    "errorCode": "LLM_JSON_PARSE_ERROR",
    "message": "AI 응답을 JSON으로 파싱할 수 없습니다.",
}


@asynccontextmanager
async def lifespan(_: FastAPI):
    global model_store
    if model_store is None:
        runtime_device = _runtime_device()
        model_store = ModelStore.create(
            dense_model_name=settings.dense_model_name,
            sparse_model_name=settings.sparse_model_name,
            device=runtime_device,
        )
    yield


app = FastAPI(lifespan=lifespan)


def _llm_json(system_prompt: str, user_prompt: str) -> dict:
    raw = provider.generate(system_prompt, user_prompt)
    try:
        return parse_json_object(raw)
    except JsonParseError as e1:
        retry_prompt = user_prompt + "\n\n" + retry_message(str(e1))
        raw_retry = provider.generate(system_prompt, retry_prompt)
        try:
            return parse_json_object(raw_retry)
        except JsonParseError:
            return PARSE_FAIL


def _runtime_device() -> str:
    configured = settings.device.strip().lower()
    if configured in {"cuda", "cpu"}:
        return configured
    if configured == "auto":
        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"
    return "cpu"


@app.get("/health")
def health():
    dense_loaded = bool(model_store and model_store.dense._model is not None)
    sparse_loaded = bool(model_store and model_store.sparse._tokenizer is not None)
    dense_fallback = bool(model_store.dense.fallback) if model_store else True
    sparse_fallback = bool(model_store.sparse.fallback) if model_store else True
    return {
        "status": "ok",
        "provider": settings.llm_provider.lower(),
        "device": _runtime_device(),
        "models": {
            "dense": {
                "configured": settings.dense_model_name,
                "loaded": dense_loaded,
                "fallback": dense_fallback,
            },
            "sparse": {
                "configured": settings.sparse_model_name,
                "loaded": sparse_loaded,
                "fallback": sparse_fallback,
            },
            "runtime": {
                "loaded": dense_loaded and sparse_loaded,
                "fallback": dense_fallback or sparse_fallback,
            },
        },
    }


@app.post("/outline")
def outline(req: OutlineRequest):
    data = _llm_json(OUTLINE_SYSTEM_PROMPT, build_outline_user_prompt(req.topicOrText))
    if data.get("success") is False and data.get("errorCode") == "LLM_JSON_PARSE_ERROR":
        return data
    return {
        "title": str(data.get("title", "")),
        "chapters": data.get("chapters", []),
    }


@app.post("/chat")
def chat(req: ChatRequest):
    history = [h.model_dump() for h in req.history]
    outline_json = json.dumps(req.outline, ensure_ascii=False)
    history_json = json.dumps(history, ensure_ascii=False)
    data = _llm_json(
        OUTLINE_CHAT_SYSTEM_PROMPT,
        build_tutor_user_prompt(req.topic, outline_json, history_json, req.message),
    )
    if data.get("success") is False and data.get("errorCode") == "LLM_JSON_PARSE_ERROR":
        return data
    return {
        "answer": str(data.get("answer", "")),
        "suggestedNextAction": str(data.get("suggestedNextAction", "")),
    }


@app.post("/questions")
def questions(req: QuestionsRequest):
    history = [h.model_dump() for h in req.history]
    data = _llm_json(
        QUESTION_SYSTEM_PROMPT,
        build_question_user_prompt(req.topic, req.outline, history),
    )
    if data.get("success") is False and data.get("errorCode") == "LLM_JSON_PARSE_ERROR":
        return data
    return {"questions": data.get("questions", [])}


@app.post("/evaluate")
def evaluate(req: EvaluateRequest):
    assert model_store is not None
    detail_scores = []
    missing_keywords = set()
    weak_concepts = set()

    for idx, q in enumerate(req.questions):
        user_answer = req.answers[idx] if idx < len(req.answers) else ""
        graded = grade_answer(model_store, q.modelAnswer, user_answer, q.keywords)
        detail_scores.append(
            {
                "questionId": q.questionId,
                "denseScore": graded["denseScore"],
                "sparseScore": graded["sparseScore"],
                "keywordScore": graded["keywordScore"],
                "finalScore": graded["finalScore"],
            }
        )
        missing_keywords.update(graded["missingKeywords"])
        weak_concepts.update(graded["weakConcepts"])

    score = round(
        sum(item["finalScore"] for item in detail_scores) / len(detail_scores), 1
    ) if detail_scores else 0.0
    level = level_from_score(score)

    feedback_data = _llm_json(
        FEEDBACK_SYSTEM_PROMPT,
        build_feedback_user_prompt(score, level, sorted(missing_keywords), sorted(weak_concepts)),
    )
    if feedback_data.get("success") is False and feedback_data.get("errorCode") == "LLM_JSON_PARSE_ERROR":
        return feedback_data

    if score >= 80:
        sm2_quality = 5
    elif score >= 60:
        sm2_quality = 3
    elif score >= 40:
        sm2_quality = 2
    else:
        sm2_quality = 0

    return {
        "score": score,
        "level": level,
        "feedback": str(feedback_data.get("feedback", "")),
        "missingKeywords": sorted(missing_keywords),
        "weakConcepts": sorted(weak_concepts),
        "detailScores": detail_scores,
        "sm2Quality": sm2_quality,
    }


@app.post("/review-content")
def review_content(req: ReviewContentRequest):
    data = _llm_json(
        REVIEW_SYSTEM_PROMPT,
        build_review_user_prompt(req.topic, req.evaluation.model_dump()),
    )
    if data.get("success") is False and data.get("errorCode") == "LLM_JSON_PARSE_ERROR":
        return data
    return {
        "flashcards": data.get("flashcards", []),
        "oxQuestions": data.get("oxQuestions", []),
        "blankQuestions": data.get("blankQuestions", []),
    }


@app.post("/review-schedule")
def review_schedule(req: ReviewScheduleRequest):
    quality, n, ef, interval = apply_sm2(req.score, req.n, req.ef, req.previousInterval)
    return {
        "quality": quality,
        "n": n,
        "ef": round(ef, 1),
        "interval": interval,
        "nextReviewDate": next_review_date(req.reviewedAt, interval),
    }
