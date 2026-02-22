from app.utils.llm import get_llm


def _fallback_generate(cv_text: str, matching: dict, country_rules: dict) -> str:
    present = matching.get("keywords_present", [])[:15]
    missing = matching.get("keywords_missing", [])[:10]
    lines = [
        "# CV Personnalise",
        "",
        "## Profil",
        "Candidat motive, avec un profil adapte a l'offre ciblee.",
        "",
        "## CV Source",
        cv_text[:4000],
        "",
        "## Mots-cles deja presents",
        ", ".join(present) if present else "Aucun mot-cle detecte.",
        "",
        "## Mots-cles a renforcer",
        ", ".join(missing) if missing else "Aucun manque majeur detecte.",
        "",
        "## Sections cibles",
        ", ".join(country_rules.get("section_order", [])),
    ]
    return "\n".join(lines).strip()


def generate_personalized_cv(cv_text: str, offer_text: str, country: str, country_rules: dict, matching: dict) -> str:
    llm = get_llm()
    if llm is None:
        return _fallback_generate(cv_text, matching, country_rules)

    prompt = f"""
Tu es un agent de personnalisation de CV.

Contexte:
- Pays cible: {country}
- Regles sections: {country_rules.get("section_order", [])}
- Sections interdites: {country_rules.get("forbidden_fields", [])}
- Pattern design: {country_rules.get("layout", {})}
- Ton attendu: {country_rules.get("tone", "")}
- Score actuel CV vs Offre: {matching.get("match_score")}
- Mots cles presents: {matching.get("keywords_present", [])}
- Mots cles manquants: {matching.get("keywords_missing", [])}

CV source:
{cv_text}

Offre:
{offer_text}

Regles strictes:
1. N'invente aucun fait, date, experience, diplome, entreprise ou competence.
2. Reorganise et reformule uniquement les informations du CV source.
3. Conserve le meme pattern d'ecriture du CV source (ton, niveau de formalite, style des phrases).
4. Conserve le meme pattern de design du CV source (structure, sections, hierarchie des titres, style des listes).
5. Optimise le CV pour l'offre sans casser le style d'origine.
6. Utilise du markdown propre:
   - Titres avec # et ##.
   - Gras avec **texte** uniquement quand pertinent.
   - Listes avec "- ".
7. Retourne uniquement du markdown.
"""
    response = llm.invoke(prompt)
    return response.content.strip()
