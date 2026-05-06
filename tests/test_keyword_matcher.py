from grading.keyword_matcher import keyword_score


def test_keyword_matcher_with_synonym():
    score, missing = keyword_score("이것은 인공지능 개념입니다", ["ai", "모델"])
    assert score == 0.5
    assert "모델" in missing


def test_keyword_matcher_auto_synonym_groups_from_reference():
    score, missing = keyword_score(
        answer="AI를 활용해 문제를 해결합니다.",
        keywords=["인공지능"],
        reference_answer="인공지능(AI)을 활용한 문제 해결",
    )
    assert score == 1.0
    assert missing == []
