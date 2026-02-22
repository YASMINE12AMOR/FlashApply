from __future__ import annotations

import re
import unicodedata
from collections import OrderedDict

ALIASES = {
    "professional summary": "Professional Summary",
    "summary": "Professional Summary",
    "profile": "Profile",
    "profil": "Profile",
    "objective": "Objective",
    "job titles": "Job Titles",
    "core skills": "Skills",
    "key skills": "Skills",
    "skills": "Skills",
    "skill highlights": "Skills",
    "competences": "Skills",
    "competences cles": "Skills",
    "technical skills": "Skills",
    "work history": "Experience",
    "professional experience": "Experience",
    "work experience": "Experience",
    "experience": "Experience",
    "experiences professionnelles": "Experience",
    "education": "Education",
    "formation": "Education",
    "certifications": "Certifications",
    "certificates": "Certifications",
    "languages": "Languages",
    "langues": "Languages",
    "distinctions": "Distinctions",
    "personal interests": "Interests",
    "centres dinteret": "Interests",
    "centres d interet": "Interests",
    "references": "References",
    "contact": "Identity & Contact",
}


def _ascii(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def _norm(text: str) -> str:
    lowered = _ascii(text).lower()
    return re.sub(r"[^a-z0-9 ]", " ", lowered).strip()


def _alias(line: str) -> str:
    cleaned = re.sub(r"\s+", " ", _norm(line))
    return ALIASES.get(cleaned, "")


def _looks_like_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(("-", "*", "•")):
        return False
    if len(stripped) > 55:
        return False
    if re.search(r"\d", stripped):
        return False
    words = [w for w in stripped.split() if w]
    if len(words) > 6:
        return False

    ascii_line = _ascii(stripped)
    letters = [c for c in ascii_line if c.isalpha()]
    if not letters:
        return False
    upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    title_like = stripped == stripped.title()
    return upper_ratio >= 0.75 or title_like


def _extract_sections(cv_text: str) -> OrderedDict[str, list[str]]:
    sections: OrderedDict[str, list[str]] = OrderedDict()
    current = "Identity & Contact"
    sections[current] = []

    for raw in cv_text.splitlines():
        line = raw.strip()
        if not line:
            continue

        mapped = _alias(line)
        if mapped:
            current = mapped
            sections.setdefault(current, [])
            continue

        if _looks_like_heading(line):
            current = _ascii(line).strip()
            sections.setdefault(current, [])
            continue

        value = line
        if value.startswith(("-", "*", "•")):
            value = value[1:].strip()
        if value:
            sections.setdefault(current, []).append(value)

    return sections


def _ordered_section_names(section_order: list[str], extracted: OrderedDict[str, list[str]]) -> list[str]:
    normalized_to_real: dict[str, str] = {}
    for real in extracted.keys():
        normalized_to_real[_norm(real)] = real

    ordered: list[str] = []
    seen: set[str] = set()

    for wanted in section_order:
        target = _alias(wanted) or wanted
        key = _norm(target)
        if key in normalized_to_real:
            real = normalized_to_real[key]
            if real not in seen:
                ordered.append(real)
                seen.add(real)

    for real in extracted.keys():
        if real not in seen:
            ordered.append(real)

    return ordered


def adapt_cv_text(
    cv_text: str,
    job_title: str,
    country: str,
    style: str,
    country_format: dict,
    missing_terms: list[str],
    focus_keywords: list[str],
) -> str:
    """Adapt CV while preserving as much source information as possible."""
    del job_title, country, style, missing_terms, focus_keywords

    extracted = _extract_sections(cv_text)
    if not extracted:
        return cv_text[:12000]

    section_order = country_format.get("section_order", [])
    ordered_names = _ordered_section_names(section_order, extracted)

    rendered: list[str] = []
    for section in ordered_names:
        items = extracted.get(section, [])
        if not items:
            continue
        rendered.append(section)
        for item in items:
            rendered.append(f"- {item}")
        rendered.append("")

    text = "\n".join(rendered).strip()
    return text if text else cv_text[:12000]
