from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScoreBreakdown:
    keyword_match: float
    length_quality: float
    final_score: float


def _length_score(cv_text: str) -> float:
    words = len(cv_text.split())
    if 200 <= words <= 1200:
        return 1.0
    if 120 <= words < 200 or 1200 < words <= 1500:
        return 0.7
    return 0.4


def compute_score(keyword_overlap: float, cv_text: str) -> ScoreBreakdown:
    length_quality = _length_score(cv_text)
    final = (keyword_overlap * 0.75) + (length_quality * 0.25)
    final_score = round(final * 100, 1)
    return ScoreBreakdown(
        keyword_match=round(keyword_overlap * 100, 1),
        length_quality=round(length_quality * 100, 1),
        final_score=final_score,
    )
