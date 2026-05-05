from pydantic import BaseModel


class EvaluateQuestionItem(BaseModel):
    questionId: int
    question: str
    modelAnswer: str
    keywords: list[str]


class EvaluateRequest(BaseModel):
    questions: list[EvaluateQuestionItem]
    answers: list[str]


class DetailScore(BaseModel):
    questionId: int
    denseScore: float
    sparseScore: float
    keywordScore: float
    finalScore: float


class EvaluateResponse(BaseModel):
    score: float
    level: str
    feedback: str
    missingKeywords: list[str]
    weakConcepts: list[str]
    detailScores: list[DetailScore]
    sm2Quality: int
