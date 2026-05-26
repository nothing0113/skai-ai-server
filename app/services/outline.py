from __future__ import annotations

import json

from app.schemas import ChatMessage, OutlineItem
from app.services.llm import LLMService


class OutlineServiceError(RuntimeError):
    """Raised when outline generation response cannot be parsed."""


class OutlineService:
    def __init__(self, llm_service: LLMService) -> None:
        self.llm_service = llm_service

    def generate(self, topic: str, depth: int, language: str = "ko") -> list[OutlineItem]:
        messages = [
            ChatMessage(
                role="system",
                content=(
                    "당신은 학습 목차 설계자입니다. "
                    "반드시 JSON 배열만 출력하세요. 코드블록, 설명 문장, 주석은 금지입니다."
                ),
            ),
            ChatMessage(
                role="user",
                content=(
                    f"주제: {topic}\n"
                    f"최대 깊이: {depth}\n"
                    f"응답 언어: {language}\n\n"
                    "다음 형식의 JSON 배열만 출력하세요:\n"
                    "[{\"level\":1,\"index\":\"1\",\"title\":\"...\"}]\n"
                    "level은 1~최대 깊이 범위의 정수, index는 1 / 1.1 / 1.1.1 형식입니다."
                ),
            ),
        ]

        raw = self.llm_service.chat(messages)
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        try:
            payload = json.loads(text)
            if not isinstance(payload, list):
                raise TypeError("outline payload must be a list")
            return [OutlineItem.model_validate(item) for item in payload]
        except Exception as exc:
            raise OutlineServiceError("Outline response parsing failed") from exc
