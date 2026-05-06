from grading.hybrid_grader import grade_answer
from grading.models import DenseModelWrapper, ModelStore, SparseModelWrapper


def _store() -> ModelStore:
    return ModelStore(
        dense=DenseModelWrapper("dummy", "cpu"),
        sparse=SparseModelWrapper("dummy", "cpu"),
    )


def test_rubric_based_partial_scoring():
    store = _store()
    result = grade_answer(
        model_store=store,
        reference_answer="CPU는 연산을 담당하고 메모리는 데이터를 저장한다.",
        user_answer="CPU가 계산을 담당한다.",
        keywords=["CPU", "메모리"],
    )
    assert 35.0 <= result["finalScore"] <= 75.0
    assert any("메모리" in c for c in result["weakConcepts"])


def test_length_penalty_for_very_short_answer():
    store = _store()
    short = grade_answer(
        model_store=store,
        reference_answer="인공지능은 데이터 학습으로 패턴을 찾고 예측한다.",
        user_answer="인공지능",
        keywords=["인공지능", "학습", "예측"],
    )
    long = grade_answer(
        model_store=store,
        reference_answer="인공지능은 데이터 학습으로 패턴을 찾고 예측한다.",
        user_answer="인공지능은 데이터를 학습해 패턴을 찾고 결과를 예측합니다.",
        keywords=["인공지능", "학습", "예측"],
    )
    assert short["finalScore"] < long["finalScore"]


def test_relevance_cap_on_unrelated_answer():
    store = _store()
    result = grade_answer(
        model_store=store,
        reference_answer="TCP는 연결지향 전송이고 3-way handshake를 사용한다.",
        user_answer="오늘 점심 메뉴는 파스타와 샐러드입니다.",
        keywords=["TCP", "handshake", "연결지향"],
    )
    assert result["finalScore"] <= 35.0


def test_graceful_fallback_with_unavailable_models(monkeypatch):
    def fail_dense_load(self):
        self._model = None
        self.fallback = True

    def fail_sparse_load(self):
        self._tokenizer = None
        self.fallback = True

    monkeypatch.setattr(DenseModelWrapper, "load", fail_dense_load)
    monkeypatch.setattr(SparseModelWrapper, "load", fail_sparse_load)

    store = ModelStore.create("missing-dense", "missing-sparse", "cpu")
    assert store.dense.fallback is True
    assert store.sparse.fallback is True

    result = grade_answer(
        model_store=store,
        reference_answer="데이터베이스 인덱스는 조회 성능을 향상한다.",
        user_answer="인덱스는 조회를 빠르게 한다.",
        keywords=["인덱스", "조회"],
    )
    assert isinstance(result["finalScore"], float)
    assert 0.0 <= result["finalScore"] <= 100.0
