from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

STOPWORDS = {
    "the", "and", "for", "with", "you", "your", "are", "from", "that", "this", "will",
    "des", "les", "une", "pour", "avec", "dans", "sur", "plus", "vos", "votre", "nous",
    "der", "die", "das", "und", "mit", "den", "ein", "eine", "fur", "auf", "ist",
}


@dataclass
class AnalysisResult:
    keywords: list[str]
    top_terms: list[tuple[str, int]]


def tokenize(text: str) -> list[str]:
    terms = re.findall(r"[A-Za-z][A-Za-z\-\+#\.]{1,}", text.lower())
    return [t for t in terms if t not in STOPWORDS and len(t) > 2]


def top_keywords(text: str, max_items: int = 20) -> AnalysisResult:
    tokens = tokenize(text)
    counts = Counter(tokens)
    top = counts.most_common(max_items)
    return AnalysisResult(keywords=[w for w, _ in top], top_terms=top)


def overlap_ratio(job_keywords: Iterable[str], cv_keywords: Iterable[str]) -> float:
    job = set(job_keywords)
    cv = set(cv_keywords)
    if not job:
        return 0.0
    return len(job & cv) / len(job)


def missing_keywords(job_keywords: Iterable[str], cv_keywords: Iterable[str], limit: int = 10) -> list[str]:
    missing = [k for k in job_keywords if k not in set(cv_keywords)]
    return missing[:limit]
