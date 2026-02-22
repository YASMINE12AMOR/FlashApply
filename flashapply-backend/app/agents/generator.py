from app.utils.llm import llm

def generate_cv(analysis: dict, cv_markdown: str, country_rules: dict):
    prompt = f"""
        Tu es l’agent FlashApply spécialisé dans la génération de CV professionnels.

        CONTEXTE :
        Analyse CV + offre :
        {analysis}

        CV original (markdown) :
        {cv_markdown}

        Règles pays :
        {country_rules}

        RÈGLES :
        1. Tu NE DOIS JAMAIS inventer de faits, dates, expériences, diplômes ou compétences.
        2. Tu DOIS réorganiser, reformuler, clarifier, mais jamais ajouter d’informations absentes du CV original.
        3. Tu DOIS suivre les sections du pays (sections_order).
        4. Tu DOIS mettre en avant les compétences réellement matching (issues de l’analyse).
        5. Tu DOIS conserver le style d’écriture du candidat.
        6. Tu DOIS produire un CV professionnel, clair, concis, optimisé pour l’offre.
        7. Tu DOIS générer uniquement du markdown, sans JSON.

        OBJECTIF :
        Générer un CV complet en markdown, conforme aux règles du pays et optimisé pour l’offre.

    """

    result = llm.invoke(prompt)
    return result.content
