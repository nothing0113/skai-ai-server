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
    return LLMConfig(
        provider="openrouter",
        base_url=_get_env_first("LLM_BASE_URL", "OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1"),
        api_key=_get_env_first("LLM_API_KEY", "OPENROUTER_API_KEY", default=""),
        model=_get_env_first("LLM_MODEL", "OPENROUTER_MODEL", default="google/gemma-3-27b-it"),
    )
