import requests

from config import Settings
from llm.base import BaseLLMClient


class LocalGemmaClient(BaseLLMClient):
    def __init__(self, settings: Settings):
        self.url = settings.local_llm_url
        self.model = settings.local_llm_model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "format": "json",
        }
        res = requests.post(self.url, json=body, timeout=60)
        res.raise_for_status()
        data = res.json()
        return data.get("message", {}).get("content", "")
