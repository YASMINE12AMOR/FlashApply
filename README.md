# ApplyFlash

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
- `src/data/countries/*.json`: un fichier JSON par pays (format CV specifique)
- `src/config/countries.py`: charge automatiquement tous les JSON des pays

## Flux
1. L'utilisateur choisit le pays + renseigne le poste vise + charge/colle son CV
2. L'offre est optionnelle (mais recommandee)
3. L'app extrait le texte
4. L'analyse detecte competences et ecarts
5. Le score est calcule
6. Le CV adapte selon le format JSON du pays + recommandations
7. Les sections sans donnees dans le CV source sont ignorees automatiquement
8. Le resultat est affiche dans Streamlit

## Lancement
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## LLM (DeepSeek)
- Le modele par defaut est defini dans `src/config/llm.py` (`DEFAULT_DEEPSEEK_MODEL`).
- Dans l'interface Streamlit, active `Use LLM rewrite (DeepSeek)`.
- Fournis la cle API soit:
  - via le champ `DEEPSEEK_API_KEY` dans la sidebar,
  - via le fichier `.env` (charge automatiquement),
  - via `.streamlit/secrets.toml`,
  - ou via la variable d'environnement `DEEPSEEK_API_KEY`.
- Si la cle est absente ou l'appel echoue, l'application utilise automatiquement le fallback heuristique.

## Stripe Premium (MVP)
- Le projet lit `STRIPE_SECRET_KEY` depuis l'environnement (serveur uniquement).
- Flux implemente:
  1. creation d'un lien Checkout Stripe,
  2. paiement utilisateur,
  3. retour avec `session_id`,
  4. verification serveur du statut `paid`,
  5. activation premium.
- Premium debloque:
  - analyses illimitees,
  - export PDF,
  - templates pays avances.
- Free plan:
  - limite d'analyses configurable via `FREE_ANALYSIS_LIMIT`,
  - templates pays limites.

Variables utiles:
```bash
STRIPE_SECRET_KEY=rk_test_xxx
APP_BASE_URL=http://localhost:8501
FREE_ANALYSIS_LIMIT=3
STRIPE_PREMIUM_PRICE_CENTS=900
STRIPE_CURRENCY=usd
```

### Eviter la saisie manuelle de la cle
Option 1 (recommandee): fichier `.env` a la racine du projet
```bash
DEEPSEEK_API_KEY=sk-xxxxxxxx
```

Option 2: fichier `.streamlit/secrets.toml`
```toml
DEEPSEEK_API_KEY = "sk-xxxxxxxx"
```

## Limites (MVP)
- Le LLM depend de la qualite du prompt et de la cle API
- Extraction PDF basique
- Score indicatif

## Evolutions
- Integrer un LLM (OpenAI/Azure) pour re-ecriture avancee
- Ajouter export DOCX/PDF du CV adapte
- Ajouter historique de candidatures et A/B testing des versions

