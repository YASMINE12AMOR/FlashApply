from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError

from src.config.countries import COUNTRY_RULES
from src.config.llm import (
    DEFAULT_DEEPSEEK_BASE_URL,
    DEFAULT_DEEPSEEK_MODEL,
    resolve_deepseek_api_key,
)
from src.core.adaptor import adapt_cv_text
from src.core.analyzer import missing_keywords, overlap_ratio, top_keywords
from src.core.exporter import text_to_pdf_bytes
from src.core.llm_agent import generate_adapted_cv_with_llm
from src.core.parsers import extract_text
from src.core.recommender import build_recommendations
from src.core.scoring import compute_score

load_dotenv()

st.set_page_config(page_title="FlashApply", page_icon=":briefcase:", layout="wide")
st.title("FlashApply - AI CV Adapter")
st.caption("Analyze a job offer, adapt your CV by country, and get a compatibility score.")

with st.sidebar:
    st.header("Configuration")
    country = st.selectbox("Target country", list(COUNTRY_RULES.keys()), index=0)
    use_llm = st.checkbox("Use LLM rewrite (DeepSeek)", value=True)
    try:
        saved_key = st.secrets.get("DEEPSEEK_API_KEY", "")
    except StreamlitSecretNotFoundError:
        saved_key = ""
    run = st.button("Run analysis", type="primary")

left, right = st.columns(2)

with left:
    st.subheader("Target Role")
    job_title = st.text_input("Job title / Poste vise", placeholder="e.g., Data Analyst")
    st.subheader("Job Offer (optional but recommended)")
    job_file = st.file_uploader("Upload job offer (.txt or .pdf)", type=["txt", "pdf"], key="job_file")
    job_text_manual = st.text_area("Or paste the job offer", height=260)

with right:
    st.subheader("Your CV")
    cv_file = st.file_uploader("Upload your CV (.txt or .pdf)", type=["txt", "pdf"], key="cv_file")
    profile_image_file = st.file_uploader(
        "Photo de profil (optionnel)",
        type=["png", "jpg", "jpeg"],
        key="profile_image_file",
    )
    cv_text_manual = st.text_area("Or paste your CV", height=260)

if run:
    job_text = extract_text(job_file.getvalue() if job_file else None, job_file.name if job_file else None, job_text_manual)
    cv_text = extract_text(cv_file.getvalue() if cv_file else None, cv_file.name if cv_file else None, cv_text_manual)
    effective_job_text = job_text if job_text else f"Target role: {job_title}"

    if not cv_text or not job_title.strip():
        st.error("Please provide both a target job title (poste) and a CV.")
        st.stop()

    job_analysis = top_keywords(effective_job_text, max_items=25)
    cv_analysis = top_keywords(cv_text, max_items=25)

    keyword_overlap = overlap_ratio(job_analysis.keywords, cv_analysis.keywords)
    missing = missing_keywords(job_analysis.keywords, cv_analysis.keywords, limit=12)

    score = compute_score(keyword_overlap, cv_text)

    rules = COUNTRY_RULES[country]
    recommendations = build_recommendations(
        missing_terms=missing,
        country_tips=rules["tips"],
        keyword_match_score=score.keyword_match,
    )

    adapted_cv = adapt_cv_text(
        cv_text=cv_text,
        job_title=job_title,
        country=country,
        style=rules["style"],
        country_format=rules.get("format", {}),
        missing_terms=missing,
        focus_keywords=rules["focus_keywords"],
    )
    llm_used = False

    if use_llm:
        api_key = resolve_deepseek_api_key(saved_key=saved_key)
        if api_key:
            try:
                llm_result = generate_adapted_cv_with_llm(
                    api_key=api_key,
                    base_url=DEFAULT_DEEPSEEK_BASE_URL,
                    model=DEFAULT_DEEPSEEK_MODEL,
                    job_title=job_title,
                    cv_text=cv_text,
                    job_text=effective_job_text,
                    country=country,
                    style=rules["style"],
                    country_format=rules.get("format", {}),
                    missing_terms=missing,
                    focus_keywords=rules["focus_keywords"],
                )
                if llm_result:
                    adapted_cv = llm_result
                    llm_used = True
            except Exception as exc:
                st.warning(f"LLM rewrite failed. Fallback used. Details: {exc}")
        else:
            st.warning("No DeepSeek API key found. Use sidebar input, .env, or .streamlit/secrets.toml.")

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Compatibility score", f"{score.final_score}%")
    c2.metric("Keyword match", f"{score.keyword_match}%")
    c3.metric("CV length quality", f"{score.length_quality}%")

    st.subheader("Top missing keywords")
    st.write(missing if missing else ["No major keyword gaps detected in top terms."])
    st.subheader("Country format loaded (JSON)")
    st.json(rules.get("format", {}))
    if not rules.get("format", {}).get("include_photo", False):
        st.caption("Photo profile ignored for this country format.")

    st.subheader("Recommendations")
    for idx, rec in enumerate(recommendations, start=1):
        st.write(f"{idx}. {rec}")

    st.subheader("Adapted CV Draft")
    st.caption(f"Generation mode: {'LLM' if llm_used else 'Heuristic fallback'}")
    st.text_area("Generated draft", adapted_cv, height=420)

    pdf_data = text_to_pdf_bytes(
        adapted_cv,
        title="FlashApply - Adapted CV",
        country=country,
        model_info=(DEFAULT_DEEPSEEK_MODEL if llm_used else "heuristic-fallback"),
        layout_mode=rules.get("format", {}).get("layout_mode", "vertical_single_column"),
        include_photo=rules.get("format", {}).get("include_photo", False),
        profile_image_bytes=(
            profile_image_file.getvalue()
            if profile_image_file and rules.get("format", {}).get("include_photo", False)
            else None
        ),
    )
    st.download_button(
        label="Download adapted CV (.pdf)",
        data=pdf_data,
        file_name="adapted_cv.pdf",
        mime="application/pdf",
    )
else:
    st.info("Select country, provide offer + CV, then click 'Run analysis'.")
