from __future__ import annotations

import math
import re
from dataclasses import dataclass

import numpy as np


TOKEN_RE = re.compile(r"[a-z0-9가-힣]+")


def _tokens(text: str) -> list[str]:
    lowered = text.lower()
    lowered = re.sub(r"([a-z0-9])([가-힣])", r"\1 \2", lowered)
    lowered = re.sub(r"([가-힣])([a-z0-9])", r"\1 \2", lowered)
    return TOKEN_RE.findall(lowered)


@dataclass
class DenseModelWrapper:
    model_name: str
    device: str
    fallback: bool = True
    _model: object | None = None

    def load(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name, device=self.device)
            self.fallback = False
        except Exception:
            self._model = None
            self.fallback = True

    def encode(self, text: str) -> np.ndarray:
        if self._model is not None:
            return np.asarray(self._model.encode(text, normalize_embeddings=True), dtype=float)
        vec = np.zeros(128, dtype=float)
        for t in _tokens(text):
            idx = hash(t) % 128
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        return vec if norm == 0 else vec / norm

    def similarity(self, a: str, b: str) -> float:
        va = self.encode(a)
        vb = self.encode(b)
        denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
        if denom == 0:
            return 0.0
        return max(0.0, min(1.0, float(np.dot(va, vb) / denom)))


@dataclass
class SparseModelWrapper:
    model_name: str
    device: str
    fallback: bool = True
    _tokenizer: object | None = None

    def load(self) -> None:
        try:
            from transformers import AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.fallback = False
        except Exception:
            self._tokenizer = None
            self.fallback = True

    def vectorize(self, text: str) -> dict[str, float]:
        toks = _tokens(text)
        if not toks:
            return {}
        tf: dict[str, float] = {}
        for t in toks:
            tf[t] = tf.get(t, 0.0) + 1.0
        max_tf = max(tf.values())
        return {k: 0.5 + 0.5 * (v / max_tf) for k, v in tf.items()}

    def similarity(self, a: str, b: str) -> float:
        va = self.vectorize(a)
        vb = self.vectorize(b)
        if not va or not vb:
            return 0.0
        common = set(va) & set(vb)
        dot = sum(va[k] * vb[k] for k in common)
        na = math.sqrt(sum(v * v for v in va.values()))
        nb = math.sqrt(sum(v * v for v in vb.values()))
        if na == 0 or nb == 0:
            return 0.0
        return max(0.0, min(1.0, dot / (na * nb)))


@dataclass
class ModelStore:
    dense: DenseModelWrapper
    sparse: SparseModelWrapper

    @classmethod
    def create(cls, dense_model_name: str, sparse_model_name: str, device: str) -> "ModelStore":
        dense = DenseModelWrapper(dense_model_name, device)
        sparse = SparseModelWrapper(sparse_model_name, device)
        dense.load()
        sparse.load()
        return cls(dense=dense, sparse=sparse)
