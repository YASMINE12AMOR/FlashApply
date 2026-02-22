import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="FlashApply", layout="wide")

st.title("⚡ FlashApply – CV Optimizer")
st.write("Analyse ton CV, compare-le à une offre, et génère un CV optimisé pour un pays donné.")

# --- 1. Upload CV ---
st.subheader("1. Upload ton CV")
uploaded_file = st.file_uploader(
    "Choisis ton CV (PDF, DOCX, PNG, JPG, TXT)",
    type=["pdf", "docx", "png", "jpg", "jpeg", "txt"]
)

# --- 2. URL de l’offre ---
st.subheader("2. URL de l’offre d’emploi")
job_offer_url = st.text_input("Colle ici l’URL de l’offre")

# --- 3. Choix du pays ---
st.subheader("3. Choisis le pays")
country = st.selectbox("Pays", ["France", "USA"])

# --- 4. Règles pays (mock pour l’instant) ---
country_rules_map = {
    "France": {
        "forbidden_sections": ["Photo", "Age"],
        "sections_order": ["Profil", "Expériences", "Compétences", "Formation"],
        "preferred_length": "1 page"
    },
    "USA": {
        "forbidden_sections": ["Photo", "Age", "Adresse complète"],
        "sections_order": ["Summary", "Experience", "Skills", "Education"],
        "preferred_length": "1 page"
    }
}
country_rules = country_rules_map.get(country, {})

# --- Bouton d’action ---
if st.button("🚀 Lancer l’analyse et la génération"):
    if not uploaded_file:
        st.error("Merci d’uploader un CV.")
        st.stop()

    if not job_offer_url:
        st.error("Merci d’entrer l’URL de l’offre.")
        st.stop()

    # 1) Lecture du CV (on le traite comme texte brut pour l’instant)
    try:
        cv_bytes = uploaded_file.read()
        cv_markdown = cv_bytes.decode("utf-8", errors="ignore")
    except Exception:
        st.error("Impossible de lire le fichier CV.")
        st.stop()

    # 2) Récupération de l’offre via Jina Reader
    try:
        jina_url = f"https://r.jina.ai/{job_offer_url}"
        job_offer_markdown = requests.get(jina_url).text
    except Exception:
        st.error("Impossible de récupérer l’offre via Jina Reader.")
        st.stop()

    # 3) Appel du backend
    payload = {
        "cv_markdown": cv_markdown,
        "job_offer_markdown": job_offer_markdown,
        "country": country,
        "country_rules": country_rules
    }

    with st.spinner("Analyse et génération en cours…"):
        try:
            resp = requests.post(f"{BACKEND_URL}/full-pipeline", json=payload)
        except Exception:
            st.error("Impossible de contacter le backend.")
            st.stop()

    if resp.status_code != 200:
        st.error(f"Erreur backend ({resp.status_code}) : {resp.text}")
        st.stop()

    data = resp.json()

    st.success("Analyse terminée ✅")

    # 4) Affichage des résultats
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Analyse CV vs Offre")
        st.json(data.get("analysis", {}))

    with col2:
        st.subheader("🌍 Conformité aux règles du pays")
        st.json(data.get("country_compliance", {}))

    st.subheader("📝 CV généré (markdown)")
    st.markdown(data.get("generated_cv", ""), unsafe_allow_html=False)
