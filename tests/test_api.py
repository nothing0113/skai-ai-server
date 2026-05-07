from __future__ import annotations

import pytest
import torch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app, create_embeddings, grade_score, health
from app.schemas import ChatMessage, EmbeddingsRequest, GradingRequest
from app.services.embeddings import EmbeddingModelError
from app.services.grading import dense_to_score, sparse_to_score
from app.services.keyword import expand_keyword, keyword_match
from app.services.llm import LLMService
from app.services.sparse import SparseModelError, SparseService


class StubEmbeddingService:
    def encode(self, texts: list[str]) -> list[list[float]]:
        if texts == ["문장1", "문장2"]:
            return [[1.0, 0.0], [0.0, 1.0]]
        if texts == ["정답", "학생 답안"]:
            return [[1.0, 0.0], [1.0, 0.0]]
        raise EmbeddingModelError("Embedding inference failed")


class StubSparseService:
    def similarity(self, a: str, b: str) -> float:
        if a == "정답" and b == "학생 답안":
            return 0.2
        raise SparseModelError("Sparse inference failed")


def test_health() -> None:
    res = health()
    assert res.model_dump() == {"status": "ok"}


def test_embeddings_shape() -> None:
    req = EmbeddingsRequest(input=["문장1", "문장2"])
    res = create_embeddings(req, embedding_service=StubEmbeddingService())

    assert res.model_dump()["data"] == [
        {"index": 0, "embedding": [1.0, 0.0]},
        {"index": 1, "embedding": [0.0, 1.0]},
    ]


def test_grading_shape_and_weights() -> None:
    req = GradingRequest(
        question="Q",
        modelAnswer="정답",
        studentAnswer="학생 답안",
        keywords=["ai", "모델"],
    )
    res = grade_score(
        req,
        embedding_service=StubEmbeddingService(),
        sparse_service=StubSparseService(),
    )

    assert res.model_dump() == {
        "scores": {
            "denseScore": 100.0,
            "sparseScore": 37.5,
            "keywordScore": 0.0,
            "totalScore": 56.2,
        },
        "evidence": {
            "matchedKeywords": [],
            "normalizedStudentAnswer": "학생 답안",
            "normalizedModelAnswer": "정답",
        },
        "feedback": None,
    }


def test_embedding_failure_is_explicit_error() -> None:
    req = EmbeddingsRequest(input=["x"])
    with pytest.raises(HTTPException) as exc_info:
        create_embeddings(req, embedding_service=StubEmbeddingService())

    assert exc_info.value.status_code == 500
    assert "Embedding inference failed" in str(exc_info.value.detail)


def test_score_thresholds() -> None:
    assert dense_to_score(0.45) == 0.0
    assert dense_to_score(0.85) == 100.0
    assert round(dense_to_score(0.65), 1) == 50.0

    assert sparse_to_score(0.05) == 0.0
    assert sparse_to_score(0.45) == 100.0
    assert round(sparse_to_score(0.25), 1) == 50.0


def test_keyword_bank_and_surface() -> None:
    score, matched, missing = keyword_match("이 답안은 인공지능과 거대 언어 모델을 다룹니다.", ["ai", "llm"])
    assert score == 1.0
    assert matched == ["ai", "llm"]
    assert missing == []

    forms = expand_keyword("LLM(거대언어모델)")
    assert "llm" in forms
    assert "거대언어모델" in forms


def test_sparse_splade_like_encode(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyTokenizer:
        def __call__(self, text: str, return_tensors: str, truncation: bool) -> dict[str, torch.Tensor]:
            assert return_tensors == "pt"
            assert truncation is True
            return {"input_ids": torch.tensor([[1, 2, 3]])}

    class DummyOut:
        logits = torch.tensor([[[0.0, 1.0], [2.0, -2.0], [1.0, 0.5]]])

    class DummyModel:
        def eval(self) -> None:
            return None

        def __call__(self, **kwargs: torch.Tensor) -> DummyOut:
            assert "input_ids" in kwargs
            return DummyOut()

    def fake_load(self: SparseService) -> None:
        self._tokenizer = DummyTokenizer()
        self._model = DummyModel()

    monkeypatch.setattr(SparseService, "_load_model", fake_load)
    service = SparseService("yjoonjang/splade-ko-v1")
    vec = service.encode("테스트")
    assert len(vec) == 2
    assert vec[0] > vec[1]


def test_llm_endpoint_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import main

    class StubLLMService:
        class Cfg:
            provider = "omlx"
            model = "supergemma4"

        config = Cfg()

        def chat(self, messages: list[ChatMessage]) -> str:
            assert messages[0].content == "안녕"
            return "안녕하세요"

    app.dependency_overrides[main.get_llm_service] = lambda: StubLLMService()
    try:
        client = TestClient(app)
        resp = client.post("/v1/llm/chat", json={"messages": [{"role": "user", "content": "안녕"}]})
        assert resp.status_code == 200
        assert resp.json() == {
            "model": "supergemma4",
            "provider": "omlx",
            "content": "안녕하세요",
        }
    finally:
        app.dependency_overrides.clear()


def test_llm_provider_config_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    from app.config import get_llm_config

    cfg = get_llm_config()
    assert cfg.provider == "openrouter"
    assert cfg.base_url == "https://openrouter.ai/api/v1"
    assert cfg.model == "google/gemma-4-26b-it"
    assert cfg.api_key == ""


def test_openrouter_defaults_and_alias_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

    from app.config import get_llm_config

    cfg = get_llm_config()
    assert cfg.provider == "openrouter"
    assert cfg.base_url == "https://openrouter.ai/api/v1"
    assert cfg.model == "google/gemma-4-26b-it"
    assert cfg.api_key == "or-key"


def test_llm_service_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import LLMConfig

    captured: dict[str, object] = {}

    class DummyResp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"choices": [{"message": {"content": "pong"}}]}

    class DummyClient:
        def __init__(self, timeout: float) -> None:
            captured["timeout"] = timeout

        def __enter__(self) -> "DummyClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, url: str, headers: dict[str, str], json: dict[str, object]) -> DummyResp:
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return DummyResp()

    monkeypatch.setattr("app.services.llm.httpx.Client", DummyClient)

    service = LLMService(LLMConfig(provider="omlx", base_url="http://127.0.0.1:11434/v1", api_key="k", model="supergemma4"))
    content = service.chat([ChatMessage(role="user", content="ping")])

    assert content == "pong"
    assert captured["url"] == "http://127.0.0.1:11434/v1/chat/completions"
    assert captured["headers"] == {"Content-Type": "application/json", "Authorization": "Bearer k"}
    assert captured["json"] == {
        "model": "supergemma4",
        "messages": [{"role": "user", "content": "ping"}],
        "temperature": 0.2,
    }
