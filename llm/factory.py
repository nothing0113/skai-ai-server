from config import Settings
from llm.base import BaseLLMClient
from llm.local_gemma import LocalGemmaClient
from llm.openrouter import OpenRouterClient


def build_provider(settings: Settings) -> BaseLLMClient:
    provider = settings.llm_provider.strip().lower()
    if provider == "local":
        return LocalGemmaClient(settings)
    if provider == "openrouter":
        return OpenRouterClient(settings)
    raise ValueError("LLM_PROVIDER must be 'local' or 'openrouter'")
