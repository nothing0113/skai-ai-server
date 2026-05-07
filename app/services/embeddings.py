from __future__ import annotations

from typing import Sequence


class EmbeddingModelError(RuntimeError):
    """Raised when the embedding model cannot be loaded or inferred."""


class EmbeddingService:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = None
        self._load_model()

    def _load_model(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        except Exception as exc:
            raise EmbeddingModelError(f"Failed to load embedding model: {self.model_name}") from exc

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        if self._model is None:
            raise EmbeddingModelError("Embedding model is not initialized")

        try:
            vectors = self._model.encode(list(texts), normalize_embeddings=True)
        except Exception as exc:
            raise EmbeddingModelError("Embedding inference failed") from exc

        return [list(map(float, vec)) for vec in vectors]
