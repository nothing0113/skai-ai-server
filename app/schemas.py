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


class KeywordWithVariants(BaseModel):
    term: str                    # 핵심 키워드 (예: "민주주의")
    variants: list[str] = []     # 동의어/유사표현 (예: ["democracy", "민주정치"])


class GradingRequest(BaseModel):
    question: str
    modelAnswer: str | None = None          # 단일 (하위 호환)
    modelAnswers: list[str] | None = None   # 복수 모범답안
    studentAnswer: str
    keywords: list[KeywordWithVariants] = []  # LLM이 생성한 키워드+동의어를 Spring에서 전달


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


class OutlineRequest(BaseModel):
    topic: str
    depth: int = 3
    language: str = "ko"


class OutlineItem(BaseModel):
    level: int
    index: str
    title: str


class OutlineResponse(BaseModel):
    topic: str
    items: list[OutlineItem]


# ── 문제 생성 (역설명) ──────────────────────────────────────────
class QuizGenerateRequest(BaseModel):
    topic: str          # 학습 주제 (e.g. "딥러닝과 머신러닝의 차이")
    count: int = 3      # 생성할 문제 수
    language: str = "ko"

class QuizItem(BaseModel):
    question: str
    modelAnswers: list[str]  # 복수 모범답안 (표현 방식 다양)
    keywords: list[str]      # 모범답안들에서 자동 추출된 핵심어

class QuizGenerateResponse(BaseModel):
    topic: str
    items: list[QuizItem]
