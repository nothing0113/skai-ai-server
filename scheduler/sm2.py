from __future__ import annotations

from datetime import date, timedelta


def quality_from_score(score: float) -> int:
    if score >= 80:
        return 5
    if score >= 60:
        return 3
    if score >= 40:
        return 2
    return 0


def apply_sm2(score: float, n: int, ef: float, previousInterval: int) -> tuple[int, int, float, int]:
    quality = quality_from_score(score)
    ef = max(1.3, ef)

    if quality < 3:
        return quality, 0, ef, 1

    if n == 0:
        interval = 1
    elif n == 1:
        interval = 6
    else:
        interval = max(1, round(previousInterval * ef))

    ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ef = max(1.3, ef)
    return quality, n + 1, ef, interval


def next_review_date(reviewed_at: str, interval: int) -> str:
    base = date.fromisoformat(reviewed_at)
    return (base + timedelta(days=interval)).isoformat()
