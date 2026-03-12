from app.agents.cv_generator_agent import generate_personalized_cv, optimize_personalized_cv
from app.agents.matching_agent import compute_matching
from app.extractors.cv_extractor import extract_cv_text
from app.extractors.job_offer_extractor import fetch_job_offer
from app.utils.country_rules import get_country_rules


def compute_country_compliance(cv_text: str, country_rules: dict) -> dict:
    compliance_score = 100
    forbidden_found = []
    lower_cv = cv_text.lower()
    for forbidden in country_rules.get("forbidden_fields", []):
        token = forbidden.replace("_", " ").lower()
        if token in lower_cv or forbidden.lower() in lower_cv:
            forbidden_found.append(forbidden)
            compliance_score -= 15

    words = max(1, len(cv_text.split()))
    estimated_pages = round(words / 500, 2)
    page_issues = []
    min_pages = country_rules.get("min_pages")
    max_pages = country_rules.get("max_pages")
    if isinstance(min_pages, (int, float)) and estimated_pages < min_pages:
        page_issues.append(f"CV trop court ({estimated_pages} pages estimees).")
        compliance_score -= 6
    if isinstance(max_pages, (int, float)) and estimated_pages > max_pages:
        page_issues.append(f"CV trop long ({estimated_pages} pages estimees).")
        compliance_score -= 6

    compliance_score = max(0, compliance_score)
    return {
        "compliance_score": compliance_score,
        "forbidden_found": forbidden_found,
        "estimated_pages": estimated_pages,
        "page_issues": page_issues,
    }


def run_pipeline(cv_file_path: str, offer_url: str, country: str) -> dict:
    cv_text = extract_cv_text(cv_file_path)
    offer_text = fetch_job_offer(offer_url)
    country_rules = get_country_rules(country)

    original_matching = compute_matching(cv_text, offer_text)
    personalized_cv = generate_personalized_cv(
        cv_text=cv_text,
        offer_text=offer_text,
        country=country,
        country_rules=country_rules,
        matching=original_matching,
    )
    personalized_matching = compute_matching(personalized_cv, offer_text)

    # If the generated CV underperforms the source CV lexically, run one targeted pass
    # to make required offer keywords more explicit without inventing content.
    if personalized_matching["match_score"] < original_matching["match_score"]:
        optimized_cv = optimize_personalized_cv(
            personalized_cv=personalized_cv,
            offer_text=offer_text,
            country=country,
            country_rules=country_rules,
            matching=personalized_matching,
        )
        optimized_matching = compute_matching(optimized_cv, offer_text)
        if optimized_matching["match_score"] >= personalized_matching["match_score"]:
            personalized_cv = optimized_cv
            personalized_matching = optimized_matching

    compliance = compute_country_compliance(personalized_cv, country_rules)

    return {
        "country": country_rules.get("country", country),
        "country_rules": country_rules,
        "cv_text": cv_text,
        "offer_text": offer_text,
        "original_matching": original_matching,
        "personalized_cv": personalized_cv,
        "personalized_matching": personalized_matching,
        "compliance": compliance,
    }
