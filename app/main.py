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
)
from app.services.embeddings import EmbeddingModelError, EmbeddingService
from app.services.grading import grade_answer
from app.services.llm import LLMService, LLMServiceError
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
    try:
        vectors = embedding_service.encode([req.modelAnswer, req.studentAnswer])
    except EmbeddingModelError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    try:
        sparse_sim = sparse_service.similarity(req.modelAnswer, req.studentAnswer)
    except SparseModelError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    scores, evidence = grade_answer(
        model_answer=req.modelAnswer,
        student_answer=req.studentAnswer,
        keywords=req.keywords,
        dense_vectors=vectors,
        sparse_similarity=sparse_sim,
    )
    return GradingResponse(scores=scores, evidence=evidence, feedback=None)


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
