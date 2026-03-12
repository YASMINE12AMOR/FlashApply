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


def _build_generation_prompt(
    cv_text: str,
    offer_text: str,
    country: str,
    country_rules: dict,
    matching: dict,
) -> str:
    present = matching.get("keywords_present", [])[:20]
    missing = matching.get("keywords_missing", [])[:15]
    target_keywords = present + [kw for kw in missing if kw not in present]

    return f"""
Tu es un agent de personnalisation de CV.

Objectif principal:
- ameliorer le score de matching final entre le CV et l'offre;
- conserver les mots-cles deja presents dans le CV source;
- reintegrer de facon naturelle les mots-cles importants de l'offre lorsqu'ils correspondent reellement au profil;
- ne jamais inventer de faits ou de competences.

Contexte:
- Pays cible: {country}
- Regles sections: {country_rules.get("section_order", [])}
- Sections interdites: {country_rules.get("forbidden_fields", [])}
- Pattern design: {country_rules.get("layout", {})}
- Ton attendu: {country_rules.get("tone", "")}
- Score actuel CV vs Offre: {matching.get("match_score")}
- Mots cles deja presents a conserver absolument: {present}
- Mots cles manquants a renforcer si justifiables: {missing}
- Liste prioritaire de mots cles a faire apparaitre clairement: {target_keywords}

CV source:
{cv_text}

Offre:
{offer_text}

Regles strictes:
1. N'invente aucun fait, date, experience, diplome, entreprise ou competence.
2. Reorganise et reformule uniquement les informations du CV source.
3. Conserve le meme pattern d'ecriture du CV source autant que possible.
4. Conserve une structure propre et compatible avec les regles pays.
5. Preserve textuellement les mots-cles deja presents dans le CV source quand ils sont pertinents.
6. Utilise de preference les termes exacts de l'offre plutot que des synonymes si ces termes correspondent reellement au profil.
7. Fais apparaitre les mots-cles utiles dans les sections visibles: Profil, Competences, Experiences, Projets.
8. N'ajoute jamais un mot-cle si cela rend le contenu faux.
9. Utilise du markdown propre:
   - Titres avec # et ##.
   - Gras avec **texte** uniquement quand pertinent.
   - Listes avec "- ".
10. Retourne uniquement du markdown.
"""


def generate_personalized_cv(cv_text: str, offer_text: str, country: str, country_rules: dict, matching: dict) -> str:
    llm = get_llm()
    if llm is None:
        return _fallback_generate(cv_text, matching, country_rules)

    prompt = _build_generation_prompt(
        cv_text=cv_text,
        offer_text=offer_text,
        country=country,
        country_rules=country_rules,
        matching=matching,
    )
    response = llm.invoke(prompt)
    return response.content.strip()


def optimize_personalized_cv(
    personalized_cv: str,
    offer_text: str,
    country: str,
    country_rules: dict,
    matching: dict,
) -> str:
    llm = get_llm()
    if llm is None:
        return personalized_cv

    present = matching.get("keywords_present", [])[:20]
    missing = matching.get("keywords_missing", [])[:15]
    prompt = f"""
Tu es un agent de correction de CV ciblee sur le matching.

Ta mission est d'ameliorer le CV personnalise ci-dessous pour augmenter le score de matching lexical avec l'offre.

Contexte:
- Pays cible: {country}
- Score actuel du CV personnalise: {matching.get("match_score")}
- Mots cles deja presents: {present}
- Mots cles encore manquants a integrer si et seulement si ils sont justifiables par le contenu: {missing}
- Regles sections: {country_rules.get("section_order", [])}
- Sections interdites: {country_rules.get("forbidden_fields", [])}

CV personnalise actuel:
{personalized_cv}

Offre:
{offer_text}

Regles strictes:
1. N'invente aucun fait ou competence.
2. Conserve la structure generale du CV personnalise actuel.
3. Ajoute ou rends plus visibles les mots-cles manquants lorsqu'ils correspondent vraiment au profil deja decrit.
4. Ne supprime pas les mots-cles deja presents.
5. Utilise les termes exacts de l'offre plutot que des synonymes quand c'est possible.
6. Retourne uniquement le CV final en markdown.
"""
    response = llm.invoke(prompt)
    return response.content.strip()
