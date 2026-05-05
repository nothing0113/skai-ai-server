from pydantic import BaseModel, Field

from schemas.tutor import ChatHistoryItem


class QuestionsRequest(BaseModel):
    topic: str = Field(min_length=1)
    outline: dict
    history: list[ChatHistoryItem] = []


class QuestionItem(BaseModel):
    questionId: int
    question: str
    modelAnswer: str
    keywords: list[str]


class QuestionsResponse(BaseModel):
    questions: list[QuestionItem]
