from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_provider: str = "local"
    local_llm_url: str = "http://localhost:11434/api/chat"
    local_llm_model: str = "gemma3"
    openrouter_api_key: str = ""
    openrouter_url: str = "https://openrouter.ai/api/v1/chat/completions"
    openrouter_model: str = "google/gemma-4-26b-a4b-it:free"
    dense_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    sparse_model_name: str = "bert-base-multilingual-cased"
    device: str = "cpu"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
