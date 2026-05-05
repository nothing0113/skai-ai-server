from grading.keyword_matcher import keyword_score


def test_keyword_matcher_with_synonym():
    score, missing = keyword_score("이것은 인공지능 개념입니다", ["ai", "모델"])
    assert score == 0.5
    assert "모델" in missing
