from __future__ import annotations

from typing import Dict


def adapt_cv_text(
    cv_text: str,
    country: str,
    style: str,
    missing_terms: list[str],
    focus_keywords: list[str],
) -> str:
    """Return a simplified adapted CV draft based on country + job gap."""
    header = [
        f"Target Country: {country}",
        f"Style: {style}",
        "",
        "Professional Summary",
        "- Results-driven profile aligned with the target role.",
        "- Strong ability to deliver outcomes in fast-paced environments.",
    ]

    if focus_keywords:
        header.append("- Country focus: " + ", ".join(focus_keywords[:5]))

    body = ["", "Core Skills"]
    if missing_terms:
        body.append("- Add/Emphasize: " + ", ".join(missing_terms[:10]))

    body.extend(
        [
            "", "Experience Highlights",
            "- Use action verbs + measurable impact (e.g., increased conversion by 22%).",
            "- Tailor each bullet to the target role requirements.",
            "", "Original CV (reference)",
            cv_text[:4000],
        ]
    )

    return "\n".join(header + body)
