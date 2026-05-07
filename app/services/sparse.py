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
            tokens = self._tokenizer(text, return_tensors="pt", truncation=True)
            with torch.no_grad():
                output = self._model(**tokens)
                vec = torch.log1p(torch.relu(output.logits)).max(dim=1).values.squeeze(0)
            return vec.detach().cpu().tolist()
        except Exception as exc:
            raise SparseModelError("Sparse inference failed") from exc

    def similarity(self, a: str, b: str) -> float:
        va = self.encode(a)
        vb = self.encode(b)
        return cosine_similarity(va, vb)


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
