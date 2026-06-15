from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException

from app.config import DENSE_MODEL_NAME, SPARSE_MODEL_NAME, get_llm_config
from app.schemas import (
    EMBEDDING_MODEL_NAME,
    EmbeddingItem,
    EmbeddingsRequest,
    EmbeddingsResponse,
    GradingRequest,
    GradingResponse,
    HealthResponse,
    LLMChatRequest,
    LLMChatResponse,
    OutlineRequest,
    OutlineResponse,
)
from app.services.embeddings import EmbeddingModelError, EmbeddingService
from app.services.grading import grade_answer
from app.services.llm import LLMService, LLMServiceError
from app.services.outline import OutlineService, OutlineServiceError
from app.services.sparse import SparseModelError, SparseService


app = FastAPI(title="skai-ai-server")
_embedding_service: EmbeddingService | None = None
_sparse_service: SparseService | None = None
_llm_service: LLMService | None = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(EMBEDDING_MODEL_NAME)
    return _embedding_service


def get_sparse_service() -> SparseService:
    global _sparse_service
    if _sparse_service is None:
        _sparse_service = SparseService()
    return _sparse_service


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(get_llm_config())
    return _llm_service


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/v1/models")
def list_models() -> dict[str, object]:
    cfg = get_llm_config()
    return {
        "embedding": DENSE_MODEL_NAME,
        "sparse": SPARSE_MODEL_NAME,
        "llm": {"provider": cfg.provider, "model": cfg.model, "baseUrl": cfg.base_url},
    }


@app.post("/v1/embeddings", response_model=EmbeddingsResponse)
def create_embeddings(
    req: EmbeddingsRequest,
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> EmbeddingsResponse:
    try:
        vectors = embedding_service.encode(req.input)
    except EmbeddingModelError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    data = [EmbeddingItem(index=i, embedding=vec) for i, vec in enumerate(vectors)]
    return EmbeddingsResponse(data=data, model=EMBEDDING_MODEL_NAME)


@app.post("/v1/grading/score", response_model=GradingResponse)
def grade_score(
    req: GradingRequest,
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    sparse_service: SparseService = Depends(get_sparse_service),
) -> GradingResponse:
    # 모범답안 목록 결정 (단일/복수 하위 호환)
    if req.modelAnswers:
        model_answers = req.modelAnswers
    elif req.modelAnswer:
        model_answers = [req.modelAnswer]
    else:
        raise HTTPException(status_code=422, detail="modelAnswer 또는 modelAnswers 중 하나는 필수입니다.")

    # keywords는 LLM이 생성해서 Spring에서 전달 — 없으면 빈 리스트 그대로 사용
    keywords = req.keywords or []

    best_scores: ScoreSet | None = None
    best_evidence: Evidence | None = None

    for answer in model_answers:
        try:
            vectors = embedding_service.encode([answer, req.studentAnswer])
        except EmbeddingModelError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        try:
            sparse_sim = sparse_service.similarity(answer, req.studentAnswer)
        except SparseModelError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        scores, evidence = grade_answer(
            model_answer=answer,
            student_answer=req.studentAnswer,
            keywords=req.keywords,
            dense_vectors=vectors,
            sparse_similarity=sparse_sim,
        )

        if best_scores is None or scores.totalScore > best_scores.totalScore:
            best_scores = scores
            best_evidence = evidence

    return GradingResponse(scores=best_scores, evidence=best_evidence, feedback=None)


@app.post("/v1/llm/chat", response_model=LLMChatResponse)
def llm_chat(
    req: LLMChatRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> LLMChatResponse:
    try:
        content = llm_service.chat(req.messages)
    except (LLMServiceError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    cfg = llm_service.config
    return LLMChatResponse(model=cfg.model, provider=cfg.provider, content=content)


@app.post("/v1/outline/generate", response_model=OutlineResponse)
def generate_outline(
    req: OutlineRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> OutlineResponse:
    outline_service = OutlineService(llm_service)
    try:
        items = outline_service.generate(topic=req.topic, depth=req.depth, language=req.language)
    except (LLMServiceError, OutlineServiceError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return OutlineResponse(topic=req.topic, items=items)
