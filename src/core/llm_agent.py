from __future__ import annotations

from openai import OpenAI


def generate_adapted_cv_with_llm(
    *,
    api_key: str,
    base_url: str,
    model: str,
    job_title: str,
    cv_text: str,
    job_text: str,
    country: str,
    style: str,
    country_format: dict,
    missing_terms: list[str],
    focus_keywords: list[str],
) -> str:
    client = OpenAI(api_key=api_key, base_url=base_url)

    system_prompt = (
        "You are an expert CV writer and recruiter advisor. "
        "Rewrite the candidate CV to maximize fit to the target role while remaining truthful. "
        "Do not invent achievements. Use concise, professional language."
    )

    section_order = country_format.get("section_order", [])
    bullet_style = country_format.get("bullet_style", "achievement-first")
    date_style = country_format.get("date_style", "MMM YYYY")
    max_pages = country_format.get("max_pages", 2)
    include_photo = country_format.get("include_photo", False)
    layout_mode = country_format.get("layout_mode", "vertical_single_column")

    user_prompt = f"""
Target country: {country}
Target role title: {job_title or "Not specified"}
Writing style: {style}
Priority country keywords: {", ".join(focus_keywords[:8]) if focus_keywords else "None"}
Missing keywords to address carefully (only if true from CV evidence): {", ".join(missing_terms[:12]) if missing_terms else "None"}
Country CV format:
- Section order: {" > ".join(section_order) if section_order else "Professional Summary > Skills > Experience > Education"}
- Bullet style: {bullet_style}
- Date format: {date_style}
- Max pages: {max_pages}
- Photo allowed: {"Yes" if include_photo else "No"}
- Layout mode: {layout_mode}

Job offer:
{job_text[:6000]}

Candidate CV:
{cv_text[:7000]}

Output requirements:
1. Return only the adapted CV text.
2. Follow the country section order, but include a section only if data exists in the source CV.
3. Use measurable achievements when present in source CV.
4. Keep length between 1 and 2 pages equivalent.
5. Do not invent missing fields or content.
6. Preserve as much factual data as possible from the source CV (projects, tools, dates, certifications, distinctions).
7. If information does not fit a standard section, place it in an Additional Information section.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return (response.choices[0].message.content or "").strip()
