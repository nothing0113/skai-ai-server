import requests

from config import Settings
from llm.base import BaseLLMClient


class OpenRouterClient(BaseLLMClient):
    def __init__(self, settings: Settings):
        self.url = settings.openrouter_url
        self.model = settings.openrouter_model
        self.api_key = settings.openrouter_api_key

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        res = requests.post(self.url, headers=headers, json=body, timeout=60)
        res.raise_for_status()
        data = res.json()
        return data["choices"][0]["message"]["content"]
