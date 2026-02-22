from __future__ import annotations

from openai import OpenAI


def generate_adapted_cv_with_llm(
    *,
    api_key: str,
    model: str,
    cv_text: str,
    job_text: str,
    country: str,
    style: str,
    missing_terms: list[str],
    focus_keywords: list[str],
) -> str:
    client = OpenAI(api_key=api_key)

    system_prompt = (
        "You are an expert CV writer and recruiter advisor. "
        "Rewrite the candidate CV to maximize fit to the target role while remaining truthful. "
        "Do not invent achievements. Use concise, professional language."
    )

    user_prompt = f"""
Target country: {country}
Writing style: {style}
Priority country keywords: {", ".join(focus_keywords[:8]) if focus_keywords else "None"}
Missing keywords to address carefully (only if true from CV evidence): {", ".join(missing_terms[:12]) if missing_terms else "None"}

Job offer:
{job_text[:6000]}

Candidate CV:
{cv_text[:7000]}

Output requirements:
1. Return only the adapted CV text.
2. Keep a clear structure: Professional Summary, Skills, Experience, Education, Certifications (if any).
3. Use measurable achievements when present in source CV.
4. Keep length between 1 and 2 pages equivalent.
"""

    response = client.chat.completions.create(
        model=model,
        temperature=0.3,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return (response.choices[0].message.content or "").strip()
