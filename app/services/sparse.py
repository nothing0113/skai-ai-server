from __future__ import annotations

import math

import torch

from app.config import SPARSE_MODEL_NAME


class SparseModelError(RuntimeError):
    """Raised when sparse model loading or inference fails."""


class SparseService:
    def __init__(self, model_name: str = SPARSE_MODEL_NAME) -> None:
        self.model_name = model_name
        self._tokenizer = None
        self._model = None
        self._load_model()

    def _load_model(self) -> None:
        try:
            from transformers import AutoModelForMaskedLM, AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForMaskedLM.from_pretrained(self.model_name)
            self._model.eval()
        except Exception as exc:
            raise SparseModelError(f"Failed to load sparse model: {self.model_name}") from exc

    def encode(self, text: str) -> list[float]:
        if self._tokenizer is None or self._model is None:
            raise SparseModelError("Sparse model is not initialized")

        try:
            tokens = self._tokenizer(
                text, return_tensors="pt", truncation=True, max_length=512
            )
            with torch.no_grad():
                output = self._model(**tokens)
                # SPLADE 집계: 시퀀스 차원(dim=1)에서 max pooling → [vocab_size]
                vec = (
                    torch.log1p(torch.relu(output.logits))
                    .max(dim=1)
                    .values
                    .squeeze(0)
                )
            return vec.detach().cpu().tolist()
        except Exception as exc:
            raise SparseModelError("Sparse inference failed") from exc

    def similarity(self, a: str, b: str) -> float:
        va = self.encode(a)
        vb = self.encode(b)
        # SPLADE는 dot product 기반 유사도를 사용해야 함
        # max(||a||², ||b||²)로 나눠서 [0, 1] 범위로 정규화
        return dot_product_similarity(va, vb)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0

    score = dot / (na * nb)
    return max(0.0, min(1.0, score))


def dot_product_similarity(a: list[float], b: list[float]) -> float:
    """SPLADE 전용 dot product 유사도.

    두 벡터의 내적을 max(||a||², ||b||²)로 나눠 [0, 1] 범위로 정규화.
    - 동일 텍스트: ~1.0
    - 무관한 텍스트: 낮은 값 (공통 어휘 노이즈 최소화)
    """
    if not a or not b:
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    if dot <= 0.0:
        return 0.0

    norm_a_sq = sum(x * x for x in a)
    norm_b_sq = sum(y * y for y in b)
    denom = max(norm_a_sq, norm_b_sq)
    if denom == 0.0:
        return 0.0

    return max(0.0, min(1.0, dot / denom))
