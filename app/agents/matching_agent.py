import re


STOP_WORDS = {
    "and",
    "the",
    "for",
    "with",
    "from",
    "that",
    "this",
    "you",
    "your",
    "des",
    "les",
    "une",
    "dans",
    "pour",
    "avec",
    "sur",
    "est",
    "are",
    "job",
    "stage",
    "alternance",
    "emploi",
}


def _extract_keywords(text: str, max_keywords: int = 40) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#\-.]{1,}", text.lower())
    freq: dict[str, int] = {}
    for token in tokens:
        if len(token) < 3 or token in STOP_WORDS:
            continue
        freq[token] = freq.get(token, 0) + 1

    sorted_tokens = sorted(freq.items(), key=lambda item: item[1], reverse=True)
    return [token for token, _ in sorted_tokens[:max_keywords]]


def compute_matching(cv_text: str, offer_text: str) -> dict:
    offer_keywords = _extract_keywords(offer_text, max_keywords=50)
    cv_text_l = cv_text.lower()

    present = [kw for kw in offer_keywords if kw in cv_text_l]
    missing = [kw for kw in offer_keywords if kw not in cv_text_l]

    score = 0
    if offer_keywords:
        score = int((len(present) / len(offer_keywords)) * 100)

    return {
        "match_score": score,
        "offer_keywords": offer_keywords,
        "keywords_present": present,
        "keywords_missing": missing,
    }
