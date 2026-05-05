from pydantic import BaseModel, Field


class ReviewEvaluation(BaseModel):
    score: float
    missingKeywords: list[str]
    weakConcepts: list[str]


class ReviewContentRequest(BaseModel):
    topic: str = Field(min_length=1)
    evaluation: ReviewEvaluation


class ReviewScheduleRequest(BaseModel):
    score: float
    n: int = 0
    ef: float = 2.5
    previousInterval: int = 0
    reviewedAt: str


class ReviewContentResponse(BaseModel):
    flashcards: list[dict]
    oxQuestions: list[dict]
    blankQuestions: list[dict]


class ReviewScheduleResponse(BaseModel):
    quality: int
    n: int
    ef: float
    interval: int
    nextReviewDate: str
