from pydantic import BaseModel, Field


class ChatHistoryItem(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    topic: str = Field(min_length=1)
    outline: dict
    history: list[ChatHistoryItem] = []
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    answer: str
    suggestedNextAction: str
