from __future__ import annotations

import re
from urllib.parse import unquote, urlparse

import streamlit as st
from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError

from src.config.countries import COUNTRY_RULES
from src.config.billing import FREE_ANALYSIS_LIMIT, FREE_COUNTRIES, PREMIUM_PRICE_CENTS
from src.config.llm import (
    DEFAULT_DEEPSEEK_BASE_URL,
    DEFAULT_DEEPSEEK_MODEL,
    resolve_deepseek_api_key,
)
from src.core.adaptor import adapt_cv_text
from src.core.analyzer import missing_keywords, overlap_ratio, top_keywords
from src.core.billing import BillingError, create_checkout_session, is_checkout_session_paid
from src.core.exporter import text_to_pdf_bytes
from src.core.llm_agent import generate_adapted_cv_with_llm
from src.core.parsers import extract_text
from src.core.recommender import build_recommendations
from src.core.scoring import compute_score


def infer_job_title_from_link(job_link: str) -> str:
    parsed = urlparse(job_link.strip())
    candidate = unquote(parsed.path.split("/")[-1] if parsed.path else "")
    candidate = re.sub(r"\.[a-zA-Z0-9]{2,4}$", "", candidate)
    candidate = re.sub(r"[-_]+", " ", candidate)
    candidate = re.sub(r"\b(job|jobs|view|offer|offre|poste|position|emploi)\b", " ", candidate, flags=re.I)
    candidate = re.sub(r"\s+", " ", candidate).strip(" -_")
    if len(candidate) < 3:
        return "Target role from offer link"
    return candidate[:80].strip().title()


load_dotenv()

st.set_page_config(page_title="ApplyFlash", page_icon=":zap:", layout="wide")

if "premium_unlocked" not in st.session_state:
    st.session_state["premium_unlocked"] = False
if "analysis_runs_used" not in st.session_state:
    st.session_state["analysis_runs_used"] = 0
if "stripe_checkout_url" not in st.session_state:
    st.session_state["stripe_checkout_url"] = ""

payment_status = st.query_params.get("payment", "")
payment_session_id = st.query_params.get("session_id", "")
if payment_status == "success" and payment_session_id and not st.session_state["premium_unlocked"]:
    try:
        if is_checkout_session_paid(payment_session_id):
            st.session_state["premium_unlocked"] = True
            st.session_state["stripe_checkout_url"] = ""
            st.success("Payment confirmed. Premium unlocked.")
    except Exception as exc:
        st.warning(f"Payment verification failed. Details: {exc}")
    finally:
        try:
            st.query_params.clear()
        except Exception:
            pass
elif payment_status == "canceled":
    st.info("Payment canceled. You can continue with the free plan.")
    try:
        st.query_params.clear()
    except Exception:
        pass

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Space+Grotesk:wght@400;500;700&display=swap');

      .stApp {
        background:
          radial-gradient(900px 520px at 8% 0%, rgba(92, 214, 255, 0.34), transparent 62%),
          radial-gradient(900px 600px at 100% 100%, rgba(93, 127, 255, 0.26), transparent 65%),
          linear-gradient(160deg, #f6fbff 0%, #eef5ff 55%, #f9fcff 100%);
      }

      [data-testid="stAppViewContainer"] > .main {
        background: transparent;
      }

      .main .block-container {
        max-width: 1160px;
        padding-top: 2.2rem;
      }

      h1, h2, h3, p, label, span, div {
        font-family: "Space Grotesk", sans-serif;
      }

      .hero {
        text-align: center;
        margin-bottom: 1.4rem;
      }

      .hero-badge {
        display: inline-block;
        border: 1px solid rgba(63, 129, 255, 0.26);
        border-radius: 999px;
        padding: 0.35rem 0.8rem;
        color: #2f62d8;
        font-size: 0.76rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        background: rgba(255, 255, 255, 0.72);
        backdrop-filter: blur(8px);
      }

      .hero h1 {
        margin: 0.8rem 0 0.4rem 0;
        font-family: "Sora", sans-serif;
        font-size: clamp(2rem, 5.2vw, 4rem);
        font-weight: 800;
        letter-spacing: -0.03em;
        color: #0e1a36;
      }

      .hero p {
        margin: 0 auto;
        max-width: 760px;
        color: #44567a;
      }

      .panel {
        border: 1px solid rgba(96, 142, 230, 0.26);
        border-radius: 16px;
        padding: 1rem 1rem 0.6rem 1rem;
        background:
          linear-gradient(160deg, rgba(255, 255, 255, 0.86), rgba(247, 251, 255, 0.95));
        box-shadow: 0 14px 36px rgba(70, 105, 173, 0.13);
        margin-bottom: 1rem;
        transition: transform 0.22s ease, box-shadow 0.22s ease;
      }

      .panel:hover {
        transform: translateY(-2px);
        box-shadow: 0 18px 42px rgba(64, 95, 156, 0.18);
      }

      .kpi-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.7rem;
        margin: 0.6rem 0 0.4rem 0;
      }

      .kpi {
        border: 1px solid rgba(96, 142, 230, 0.22);
        border-radius: 12px;
        padding: 0.7rem 0.75rem;
        text-align: center;
        background: rgba(255, 255, 255, 0.74);
      }

      .kpi .value {
        color: #1f4fcc;
        font-size: 1.1rem;
        font-weight: 700;
      }

      .kpi .label {
        color: #5a6e93;
        font-size: 0.73rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
      }

      [data-testid="stSidebar"], [data-testid="collapsedControl"] {
        display: none !important;
      }

      .stButton > button {
        border-radius: 12px;
        border: 1px solid rgba(56, 122, 232, 0.55);
        background: linear-gradient(135deg, #2e73f0, #55a5ff);
        color: #ffffff;
        font-weight: 700;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
      }

      .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 24px rgba(72, 137, 243, 0.3);
      }

      .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(255, 255, 255, 0.92) !important;
        border-color: rgba(95, 140, 221, 0.35) !important;
        color: #15203b !important;
      }

      .stMarkdown, .stCaption, .stTextInput label, .stTextArea label, .stFileUploader label, .stSelectbox label {
        color: #233255 !important;
      }

      .config-title {
        margin-bottom: 0.5rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <span class="hero-badge">AI CV Matching Studio</span>
      <h1>ApplyFlash</h1>
      <p>Collez le lien de l'offre, chargez votre CV et obtenez une version adaptee avec un score de matching clair et rapide.</p>
    </div>
    <div class="kpi-row">
      <div class="kpi"><div class="value">5</div><div class="label">Pays preconfigures</div></div>
      <div class="kpi"><div class="value">~30s</div><div class="label">Duree moyenne</div></div>
      <div class="kpi"><div class="value">IA + Regles</div><div class="label">Moteur hybride</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="panel">', unsafe_allow_html=True)
st.subheader("Configuration")
cfg1, cfg2, cfg3 = st.columns([1.5, 1, 1])
all_countries = list(COUNTRY_RULES.keys())
if st.session_state["premium_unlocked"]:
    selectable_countries = all_countries
else:
    selectable_countries = [c for c in all_countries if c in FREE_COUNTRIES]
if not selectable_countries:
    selectable_countries = all_countries
with cfg1:
    country = st.selectbox("Target country", selectable_countries, index=0)
with cfg2:
    use_llm = st.checkbox("Use LLM rewrite", value=True)
with cfg3:
    st.write("")
    st.write("")
    run = st.button("Run analysis", type="primary", use_container_width=True)
try:
    saved_key = st.secrets.get("DEEPSEEK_API_KEY", "")
except StreamlitSecretNotFoundError:
    saved_key = ""
st.markdown("</div>", unsafe_allow_html=True)

if st.session_state["premium_unlocked"]:
    st.success("Premium plan active: unlimited analyses, premium PDF export, all country templates.")
else:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Unlock Premium")
    st.write(
        f"Free plan: {FREE_ANALYSIS_LIMIT} analyses max, limited country templates, and no PDF export."
    )
    st.write(
        f"Premium unlocks unlimited analyses, PDF export, and all country templates for ${PREMIUM_PRICE_CENTS / 100:.2f}."
    )
    billing_email = st.text_input("Receipt email (optional)", placeholder="you@example.com", key="billing_email")
    if st.button("Create payment link", use_container_width=True):
        try:
            checkout = create_checkout_session(email=billing_email)
            st.session_state["stripe_checkout_url"] = checkout.checkout_url
        except BillingError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Could not create payment link. Details: {exc}")
    if st.session_state["stripe_checkout_url"]:
        st.link_button("Open secure checkout", st.session_state["stripe_checkout_url"], use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

left, right = st.columns(2)

with left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Offre d'emploi")
    job_link = st.text_input(
        "Lien de l'offre",
        placeholder="https://www.linkedin.com/jobs/view/...",
    )
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Votre CV actuel")
    cv_file = st.file_uploader("Upload your CV (.txt or .pdf)", type=["txt", "pdf"], key="cv_file")
    cv_text_manual = st.text_area("Or paste your CV", height=260)
    st.markdown("</div>", unsafe_allow_html=True)

if run:
    if not st.session_state["premium_unlocked"] and st.session_state["analysis_runs_used"] >= FREE_ANALYSIS_LIMIT:
        st.error("Free analysis limit reached. Unlock Premium to continue.")
        st.stop()

    cv_text = extract_text(cv_file.getvalue() if cv_file else None, cv_file.name if cv_file else None, cv_text_manual)
    cleaned_link = (job_link or "").strip()
    job_title = infer_job_title_from_link(cleaned_link)
    effective_job_text = f"Job offer link: {cleaned_link}\nInferred role: {job_title}"

    if not cv_text or not cleaned_link:
        st.error("Please provide both a job offer link and a CV.")
        st.stop()

    job_analysis = top_keywords(effective_job_text, max_items=25)
    cv_analysis = top_keywords(cv_text, max_items=25)

    missing = missing_keywords(job_analysis.keywords, cv_analysis.keywords, limit=12)

    keyword_overlap = overlap_ratio(job_analysis.keywords, cv_analysis.keywords)
    score = compute_score(keyword_overlap, cv_text)
    st.session_state["analysis_runs_used"] += 1

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

    st.subheader("Recommendations")
    for idx, rec in enumerate(recommendations, start=1):
        st.write(f"{idx}. {rec}")

    st.subheader("Adapted CV Draft")
    st.caption(f"Generation mode: {'LLM' if llm_used else 'Heuristic fallback'}")
    st.text_area("Generated draft", adapted_cv, height=420)

    if st.session_state["premium_unlocked"]:
        pdf_data = text_to_pdf_bytes(
            adapted_cv,
            title="ApplyFlash - Adapted CV",
            country=country,
            model_info=(DEFAULT_DEEPSEEK_MODEL if llm_used else "heuristic-fallback"),
            layout_mode=rules.get("format", {}).get("layout_mode", "vertical_single_column"),
            include_photo=False,
            profile_image_bytes=None,
        )
        st.download_button(
            label="Download adapted CV (.pdf)",
            data=pdf_data,
            file_name="adapted_cv.pdf",
            mime="application/pdf",
        )
    else:
        st.info("PDF export is a Premium feature. Unlock premium to download the adapted CV.")
else:
    if st.session_state["premium_unlocked"]:
        st.info("Select country, add the job offer link + CV, then click 'Run analysis'.")
    else:
        st.info(
            f"Free plan usage: {st.session_state['analysis_runs_used']}/{FREE_ANALYSIS_LIMIT} analyses."
        )
