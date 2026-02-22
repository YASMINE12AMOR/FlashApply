import json
from app.utils.llm import llm

def analyze_cv_and_job(cv_markdown: str, job_offer_markdown: str, country: str, country_rules: dict):
    prompt = f"""
                    Tu es l’agent FlashApply spécialisé dans l’analyse croisée entre un CV et une offre d’emploi.

                CONTEXTE :
                CV markdown :
                {cv_markdown}

                Offre d’emploi markdown :
                {job_offer_markdown}

                Pays : {country}
                Règles pays :
                {country_rules}

                RÈGLES ABSOLUES :
                1. Tu NE DOIS JAMAIS inventer de compétences, expériences, dates, diplômes ou réalisations.
                2. Tu NE DOIS utiliser que les informations réellement présentes dans le CV et l’offre.
                3. Tu DOIS respecter les conventions du pays {country} (issues de {country_rules}).
                4. Tu DOIS identifier uniquement les correspondances réelles entre CV et offre.
                5. Si une information n’est pas dans le CV, tu DOIS la considérer comme manquante.
                6. Tu DOIS rester strict, factuel, et ne jamais extrapoler.

                OBJECTIF :
                Analyser le CV par rapport à l’offre et retourner un JSON structuré, adapté à l’offre.

                FORMAT DE SORTIE STRICT (JSON) :

                {
                "match_score": <nombre entre 0 et 100>,
                "cv_relevant_skills": [],
                "cv_missing_skills": [],
                "relevant_experiences": [],
                "ats_keywords_present": [],
                "ats_keywords_missing": [],
                "country_adjustments": "",
                "recommendations": []
                }

        """

    result = llm.invoke(prompt)
    return json.loads(result.content)
