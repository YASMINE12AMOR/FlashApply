# FlashApply Streamlit App

Application agentique qui prend:
- un CV (PDF/DOCX/TXT/Image),
- un lien d'offre (emploi/stage/alternance),
- un pays cible,

et retourne:
- un CV personnalise,
- un score de matching CV original vs offre,
- un score de matching CV personnalise vs offre,
- un score de conformite pays.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration optionnelle LLM

Creez un fichier `.env`:

```env
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini
```

Sans cle OpenAI, l'application fonctionne en mode fallback (sans LLM).

## Lancement

```bash
streamlit run streamlit_app.py
```

Puis ouvrez `http://localhost:8501`.
