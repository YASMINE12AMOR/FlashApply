DEFAULT_COUNTRY_RULES = {
    "france": {
        "sections_order": [
            "Titre",
            "Profil",
            "Experiences",
            "Competences",
            "Formation",
            "Langues",
            "Projets",
        ],
        "forbidden_sections": ["Situation familiale detaillee", "Religion"],
    },
    "canada": {
        "sections_order": [
            "Title",
            "Summary",
            "Skills",
            "Work Experience",
            "Education",
            "Projects",
        ],
        "forbidden_sections": ["Photo", "Date of birth", "Marital status"],
    },
    "germany": {
        "sections_order": [
            "Title",
            "Summary",
            "Work Experience",
            "Skills",
            "Education",
            "Projects",
        ],
        "forbidden_sections": ["Salary expectation"],
    },
}


def get_country_rules(country: str) -> dict:
    return DEFAULT_COUNTRY_RULES.get(country.lower().strip(), DEFAULT_COUNTRY_RULES["france"])
