from __future__ import annotations

import streamlit as st

from src.config.countries import COUNTRY_RULES
from src.config.llm import DEFAULT_OPENAI_MODEL, resolve_openai_api_key
from src.core.adaptor import adapt_cv_text
from src.core.analyzer import missing_keywords, overlap_ratio, top_keywords
from src.core.exporter import text_to_pdf_bytes
from src.core.llm_agent import generate_adapted_cv_with_llm
from src.core.parsers import extract_text
from src.core.recommender import build_recommendations
from src.core.scoring import compute_score


st.set_page_config(page_title="FlashApply", page_icon=":briefcase:", layout="wide")
st.title("FlashApply - AI CV Adapter")
st.caption("Analyze a job offer, adapt your CV by country, and get a compatibility score.")

with st.sidebar:
    st.header("Configuration")
    country = st.selectbox("Target country", list(COUNTRY_RULES.keys()), index=0)
    use_llm = st.checkbox("Use LLM rewrite (OpenAI)", value=True)
    llm_model = st.text_input("LLM model", value=DEFAULT_OPENAI_MODEL, disabled=not use_llm)
    llm_api_key_input = st.text_input(
        "OPENAI_API_KEY",
        type="password",
        placeholder="sk-...",
        disabled=not use_llm,
    )
    run = st.button("Run analysis", type="primary")

left, right = st.columns(2)

with left:
    st.subheader("Job Offer")
    job_file = st.file_uploader("Upload job offer (.txt or .pdf)", type=["txt", "pdf"], key="job_file")
    job_text_manual = st.text_area("Or paste the job offer", height=260)

with right:
    st.subheader("Your CV")
    cv_file = st.file_uploader("Upload your CV (.txt or .pdf)", type=["txt", "pdf"], key="cv_file")
    cv_text_manual = st.text_area("Or paste your CV", height=260)

if run:
    job_text = extract_text(job_file.getvalue() if job_file else None, job_file.name if job_file else None, job_text_manual)
    cv_text = extract_text(cv_file.getvalue() if cv_file else None, cv_file.name if cv_file else None, cv_text_manual)

    if not job_text or not cv_text:
        st.error("Please provide both a job offer and a CV (file or pasted text).")
        st.stop()

    job_analysis = top_keywords(job_text, max_items=25)
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
        country=country,
        style=rules["style"],
        missing_terms=missing,
        focus_keywords=rules["focus_keywords"],
    )
    llm_used = False

    if use_llm:
        api_key = resolve_openai_api_key(llm_api_key_input)
        if api_key:
            try:
                llm_result = generate_adapted_cv_with_llm(
                    api_key=api_key,
                    model=llm_model.strip() or DEFAULT_OPENAI_MODEL,
                    cv_text=cv_text,
                    job_text=job_text,
                    country=country,
                    style=rules["style"],
                    missing_terms=missing,
                    focus_keywords=rules["focus_keywords"],
                )
                if llm_result:
                    adapted_cv = llm_result
                    llm_used = True
            except Exception as exc:
                st.warning(f"LLM rewrite failed. Fallback used. Details: {exc}")
        else:
            st.warning("No OpenAI API key provided. Fallback heuristic rewrite used.")

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Compatibility score", f"{score.final_score}%")
    c2.metric("Keyword match", f"{score.keyword_match}%")
    c3.metric("CV length quality", f"{score.length_quality}%")

    st.subheader("Top missing keywords")
    st.write(missing if missing else ["No major keyword gaps detected in top terms."])

    st.subheader("Recommendations")
    for idx, rec in enumerate(recommendations, start=1):
        st.write(f"{idx}. {rec}")

    st.subheader("Adapted CV Draft")
    st.caption(f"Generation mode: {'LLM' if llm_used else 'Heuristic fallback'}")
    st.text_area("Generated draft", adapted_cv, height=420)

    pdf_data = text_to_pdf_bytes(adapted_cv, title="FlashApply - Adapted CV")
    st.download_button(
        label="Download adapted CV (.pdf)",
        data=pdf_data,
        file_name="adapted_cv.pdf",
        mime="application/pdf",
    )
else:
    st.info("Select country, provide offer + CV, then click 'Run analysis'.")
