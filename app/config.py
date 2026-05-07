from __future__ import annotations

import os
from dataclasses import dataclass

DENSE_MODEL_NAME = "dragonkue/snowflake-arctic-embed-l-v2.0-ko"
SPARSE_MODEL_NAME = "yjoonjang/splade-ko-v1"


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    base_url: str
    api_key: str
    model: str


def _get_env_first(*keys: str, default: str = "") -> str:
    for key in keys:
        value = os.getenv(key)
        if value is not None:
            return value.strip()
    return default


def get_llm_config() -> LLMConfig:
    provider = os.getenv("LLM_PROVIDER", "openrouter").strip().lower() or "openrouter"
    if provider not in {"omlx", "openrouter"}:
        raise ValueError("LLM_PROVIDER must be one of: omlx, openrouter")

    if provider == "omlx":
        default_base = "http://127.0.0.1:11434/v1"
        default_model = "supergemma4"
        default_key = "omlx-local"
    else:
        default_base = "https://openrouter.ai/api/v1"
        default_model = "google/gemma-4-26b-it"
        default_key = ""

    return LLMConfig(
        provider=provider,
        base_url=_get_env_first("LLM_BASE_URL", "OPENROUTER_BASE_URL", default=default_base),
        api_key=_get_env_first("LLM_API_KEY", "OPENROUTER_API_KEY", default=default_key),
        model=_get_env_first("LLM_MODEL", "OPENROUTER_MODEL", default=default_model),
    )
