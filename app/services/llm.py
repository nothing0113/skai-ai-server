from __future__ import annotations

from typing import Any

import httpx

from app.config import LLMConfig
from app.schemas import ChatMessage


class LLMServiceError(RuntimeError):
    """Raised when configured LLM provider cannot be reached or returns invalid data."""


class LLMService:
    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    def chat(self, messages: list[ChatMessage]) -> str:
        payload = {
            "model": self.config.model,
            "messages": [m.model_dump() for m in messages],
            "temperature": 0.2,
        }
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        url = self.config.base_url.rstrip("/") + "/chat/completions"
        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                body: dict[str, Any] = response.json()
        except Exception as exc:
            raise LLMServiceError(f"LLM request failed for provider={self.config.provider}") from exc

        try:
            return str(body["choices"][0]["message"]["content"])
        except Exception as exc:
            raise LLMServiceError("LLM response schema invalid") from exc
