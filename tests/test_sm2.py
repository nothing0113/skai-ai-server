from scheduler.sm2 import apply_sm2, next_review_date, quality_from_score


def test_quality_from_score_thresholds_exact():
    assert quality_from_score(80) == 5
    assert quality_from_score(79.9) == 3
    assert quality_from_score(60) == 3
    assert quality_from_score(59.9) == 2
    assert quality_from_score(40) == 2
    assert quality_from_score(39.9) == 0


def test_apply_sm2_quality_below_3_resets_n_and_interval_to_1():
    quality, n, ef, interval = apply_sm2(39.9, 4, 2.5, 12)

    assert quality == 0
    assert n == 0
    assert ef == 2.5
    assert interval == 1


def test_apply_sm2_first_and_second_success_intervals_are_exact():
    q1, n1, ef1, i1 = apply_sm2(80, 0, 2.5, 0)
    assert q1 == 5
    assert n1 == 1
    assert ef1 == 2.6
    assert i1 == 1

    q2, n2, ef2, i2 = apply_sm2(60, 1, ef1, i1)
    assert q2 == 3
    assert n2 == 2
    assert ef2 == 2.46
    assert i2 == 6


def test_apply_sm2_third_plus_interval_uses_round_previous_times_ef():
    quality, n, ef, interval = apply_sm2(80, 2, 2.46, 6)

    assert quality == 5
    assert n == 3
    assert interval == 15
    assert ef == 2.56


def test_next_review_date_adds_interval_days():
    assert next_review_date("2026-05-05", 1) == "2026-05-06"
    assert next_review_date("2026-05-05", 15) == "2026-05-20"
