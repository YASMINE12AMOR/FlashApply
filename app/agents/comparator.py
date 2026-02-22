def compare_with_country_rules(analysis: dict, country_rules: dict, cv_markdown: str):
    compliance = {
        "forbidden_sections_present": [],
        "missing_required_sections": [],
        "formatting_issues": [],
        "compliance_score": 100
    }

    for section in country_rules.get("forbidden_sections", []):
        if section.lower() in cv_markdown.lower():
            compliance["forbidden_sections_present"].append(section)
            compliance["compliance_score"] -= 10

    for section in country_rules.get("sections_order", []):
        if section.lower() not in cv_markdown.lower():
            compliance["missing_required_sections"].append(section)
            compliance["compliance_score"] -= 5

    if country_rules.get("preferred_length") == "1 page":
        if len(cv_markdown.split()) > 600:
            compliance["formatting_issues"].append("CV trop long (>1 page)")
            compliance["compliance_score"] -= 10

    return compliance
