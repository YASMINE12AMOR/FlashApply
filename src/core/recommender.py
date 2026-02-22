from __future__ import annotations

from typing import Any


def build_recommendations(
    missing_terms: list[str], country_tips: list[str], keyword_match_score: float
) -> list[str]:
    recommendations: list[str] = []

    if keyword_match_score < 50:
        recommendations.append(
            "Rework your experience bullets to include more role-specific skills and tools from the offer."
        )
    elif keyword_match_score < 70:
        recommendations.append(
            "Strengthen alignment by explicitly mapping your achievements to the job requirements."
        )
    else:
        recommendations.append(
            "Your profile is already aligned; improve clarity with stronger measurable achievements."
        )

    if missing_terms:
        recommendations.append(
            "Add evidence for missing keywords: " + ", ".join(missing_terms[:8])
        )

    recommendations.extend(country_tips[:2])
    return recommendations
