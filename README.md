# FlashApply

Application IA simple pour:
- analyser une offre d'emploi
- analyser un CV
- adapter le CV selon le pays et l'offre
- calculer un score de compatibilite
- proposer des recommandations actionnables

## Architecture simple

### 1) Frontend (Streamlit)
- `app.py`
- Role: interface utilisateur (upload CV/offre, choix pays, affichage score + recommandations + CV adapte)

### 2) Coeur metier (Python modules)
- `src/core/parsers.py`: extraction de texte (TXT/PDF)
- `src/core/analyzer.py`: extraction de competences/mots-cles depuis CV et offre
- `src/core/scoring.py`: calcul du score de compatibilite
- `src/core/adaptor.py`: adaptation du CV selon pays et offre
- `src/core/recommender.py`: recommandations prioritaires

### 3) Configuration
- `src/config/countries.py`: regles simplifiees par pays (USA, Canada, France, Allemagne, UK)

## Flux
1. L'utilisateur charge son CV + colle/charge une offre
2. L'app extrait le texte
3. L'analyse detecte competences et ecarts
4. Le score est calcule
5. Le CV adapte et les recommandations sont generes
6. Le resultat est affiche dans Streamlit

## Lancement
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## LLM (OpenAI)
- Le modele par defaut est defini dans `src/config/llm.py` (`DEFAULT_OPENAI_MODEL`).
- Dans l'interface Streamlit, active `Use LLM rewrite (OpenAI)`.
- Fournis la cle API soit:
  - via le champ `OPENAI_API_KEY` dans la sidebar,
  - soit via la variable d'environnement `OPENAI_API_KEY`.
- Si la cle est absente ou l'appel echoue, l'application utilise automatiquement le fallback heuristique.

## Limites (MVP)
- Le LLM depend de la qualite du prompt et de la cle API
- Extraction PDF basique
- Score indicatif

## Evolutions
- Integrer un LLM (OpenAI/Azure) pour re-ecriture avancee
- Ajouter export DOCX/PDF du CV adapte
- Ajouter historique de candidatures et A/B testing des versions
