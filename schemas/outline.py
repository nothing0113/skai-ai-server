from pydantic import BaseModel, Field


class Chapter(BaseModel):
    order: int
    title: str
    keywords: list[str]


class OutlineRequest(BaseModel):
    topicOrText: str = Field(min_length=1)


class OutlineResponse(BaseModel):
    title: str
    chapters: list[Chapter]
