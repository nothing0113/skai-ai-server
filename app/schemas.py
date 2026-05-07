from __future__ import annotations

from pydantic import BaseModel

from app.config import DENSE_MODEL_NAME

EMBEDDING_MODEL_NAME = DENSE_MODEL_NAME


class HealthResponse(BaseModel):
    status: str


class EmbeddingsRequest(BaseModel):
    input: list[str]


class EmbeddingItem(BaseModel):
    index: int
    embedding: list[float]


class EmbeddingsResponse(BaseModel):
    data: list[EmbeddingItem]
    model: str


class GradingRequest(BaseModel):
    question: str
    modelAnswer: str
    studentAnswer: str
    keywords: list[str]


class ScoreSet(BaseModel):
    denseScore: float
    sparseScore: float
    keywordScore: float
    totalScore: float


class Evidence(BaseModel):
    matchedKeywords: list[str]
    normalizedStudentAnswer: str
    normalizedModelAnswer: str


class GradingResponse(BaseModel):
    scores: ScoreSet
    evidence: Evidence
    feedback: None = None


class ChatMessage(BaseModel):
    role: str
    content: str


class LLMChatRequest(BaseModel):
    messages: list[ChatMessage]


class LLMChatResponse(BaseModel):
    model: str
    provider: str
    content: str
