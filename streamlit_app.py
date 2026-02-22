import os
import re
import tempfile
from html import escape
from io import BytesIO
from pathlib import Path

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.platypus.doctemplate import LayoutError

from app.agents.pipeline_agent import run_pipeline
from app.utils.stripe_payments import create_payment_link
from app.utils.country_rules import get_available_countries, get_country_rules


st.set_page_config(page_title="FlashApply", page_icon=":briefcase:", layout="wide")


def _format_inline(md_line: str) -> str:
    safe = escape(md_line)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
    safe = re.sub(r"\*(.+?)\*", r"<i>\1</i>", safe)
    return safe


def _make_styles(country: str):
    styles = getSampleStyleSheet()
    if country.lower() == "germany":
        body_size = 10
        h1_size = 15
        h2_size = 12
    elif country.lower() == "canada":
        body_size = 10.5
        h1_size = 16
        h2_size = 12.5
    else:
        body_size = 10
        h1_size = 15
        h2_size = 12

    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=body_size,
        leading=14,
        spaceAfter=6,
    )
    h1 = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=h1_size,
        leading=20,
        spaceAfter=10,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=h2_size,
        leading=16,
        spaceBefore=6,
        spaceAfter=8,
    )
    return body, h1, h2


def _parse_markdown_sections(text: str):
    sections = []
    current_title = "root"
    current_lines = []

    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.lstrip()
        if stripped.startswith("# ") or stripped.startswith("## ") or stripped.startswith("### "):
            if current_lines:
                sections.append((current_title, current_lines))
            current_title = stripped.lstrip("#").strip().lower()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, current_lines))
    return sections


def _build_story_from_lines(lines, body_style, h1_style, h2_style):
    story = []
    for raw_line in lines:
        line = raw_line.rstrip()
        if not line.strip():
            story.append(Spacer(1, 6))
            continue
        stripped = line.lstrip()

        if stripped.startswith("# "):
            story.append(Paragraph(_format_inline(stripped[2:].strip()), h1_style))
            continue
        if stripped.startswith("## "):
            story.append(Paragraph(_format_inline(stripped[3:].strip()), h2_style))
            continue
        if stripped.startswith("### "):
            story.append(Paragraph(_format_inline(stripped[4:].strip()), h2_style))
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            story.append(Paragraph(_format_inline(stripped[2:].strip()), body_style, bulletText="*"))
            continue

        story.append(Paragraph(_format_inline(stripped), body_style))
    return story


def _build_france_two_column_story(text: str, body_style, h1_style, h2_style):
    sections = _parse_markdown_sections(text)
    sidebar_keys = {
        "contact",
        "details",
        "core competencies",
        "technical summary",
        "competences",
        "skills",
        "langues",
        "languages",
    }

    left_lines = []
    right_lines = []

    for title, lines in sections:
        target = left_lines if any(key in title for key in sidebar_keys) else right_lines
        target.append(f"## {title.upper()}" if title != "root" else "")
        target.extend(lines)
        target.append("")

    left_story = _build_story_from_lines(left_lines, body_style, h1_style, h2_style)
    right_story = _build_story_from_lines(right_lines, body_style, h1_style, h2_style)
    table = Table([[left_story, right_story]], colWidths=[170, 340], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("LINEAFTER", (0, 0), (0, 0), 0.5, colors.lightgrey),
            ]
        )
    )
    return [table]


def build_pdf_from_text(text: str, country_rules: dict) -> bytes:
    country = country_rules.get("country", "")
    body_style, h1_style, h2_style = _make_styles(country)

    def _build_doc(flowables):
        local_buffer = BytesIO()
        local_doc = SimpleDocTemplate(
            local_buffer,
            pagesize=A4,
            leftMargin=30,
            rightMargin=30,
            topMargin=30,
            bottomMargin=30,
        )
        local_doc.build(flowables)
        local_buffer.seek(0)
        return local_buffer.getvalue()

    if country.lower() == "france":
        try:
            story = _build_france_two_column_story(text, body_style, h1_style, h2_style)
            return _build_doc(story)
        except LayoutError:
            pass

    story = _build_story_from_lines(text.splitlines(), body_style, h1_style, h2_style)
    return _build_doc(story)


def _inject_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');
        html, body, [class*="css"]  { font-family: 'Manrope', sans-serif; }

        .stApp {
            background:
              radial-gradient(1200px 600px at 80% 120%, rgba(171, 74, 255, 0.22), transparent 65%),
              radial-gradient(1000px 500px at 20% -10%, rgba(36, 76, 255, 0.20), transparent 55%),
              linear-gradient(135deg, #060814 0%, #0b1022 40%, #090d1d 100%);
            color: #eef0ff;
        }

        .main .block-container {
            max-width: 1280px;
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }

        .panel {
            background: linear-gradient(180deg, rgba(18,22,46,0.82), rgba(10,13,30,0.82));
            border: 1px solid rgba(120, 130, 255, 0.28);
            border-radius: 18px;
            box-shadow: 0 12px 34px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255,255,255,0.06);
            padding: 1.05rem 1.2rem;
            margin-bottom: 1rem;
        }

        .hero {
            text-align: center;
            padding: 0.65rem 0.2rem 0.35rem 0.2rem;
        }

        .hero-badge {
            display: inline-block;
            border: 1px solid rgba(124, 138, 255, 0.55);
            color: #9ca8ff;
            border-radius: 999px;
            padding: 0.35rem 0.9rem;
            font-size: 0.86rem;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            margin-bottom: 0.9rem;
            background: rgba(42, 52, 126, 0.25);
        }

        .hero h1 {
            margin: 0;
            font-size: 4.2rem;
            line-height: 1.02;
            font-weight: 800;
            letter-spacing: 0.01em;
            color: #c8b7ff;
            font-family: "Times New Roman", Georgia, serif;
        }

        .hero p {
            margin: 0.9rem auto 0 auto;
            color: #a3acd6;
            font-size: 1.2rem;
            max-width: 780px;
            line-height: 1.55;
        }

        .card-title {
            margin: 0;
            font-size: 1.18rem;
            font-weight: 700;
            color: #f4f6ff;
        }

        .card-subtitle {
            margin: 0.2rem 0 0.8rem 0;
            color: #98a3d8;
            font-size: 0.93rem;
        }

        .kpi {
            text-align: center;
            padding: 0.7rem 0.8rem;
            border-radius: 14px;
            border: 1px solid rgba(130, 140, 255, 0.22);
            background: rgba(15, 18, 35, 0.75);
            min-height: 88px;
        }

        .kpi .label {
            color: #9ea8d7;
            font-size: 0.78rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .kpi .value {
            color: #7ae2ff;
            font-size: 2rem;
            font-weight: 800;
            margin-top: 0.2rem;
        }

        .placeholder {
            min-height: 320px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            color: #8f98c7;
            gap: 0.65rem;
        }

        .placeholder .star {
            font-size: 1.7rem;
            color: #b9a8ff;
        }

        .stFileUploader, .stTextInput > div > div, .stSelectbox > div > div {
            border-radius: 12px !important;
        }

        div.stButton > button {
            width: 100%;
            border-radius: 12px;
            font-weight: 700;
            border: 1px solid rgba(105, 120, 255, 0.45);
            background: linear-gradient(90deg, #5e6bff, #8b5cf6);
            color: white;
        }

        div.stButton > button:hover {
            filter: brightness(1.07);
            border-color: rgba(145, 158, 255, 0.8);
        }
        @media (max-width: 900px) {
            .hero h1 { font-size: 2.65rem; }
            .hero p { font-size: 1.05rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _find_logo_path() -> str | None:
    candidates = [
        os.getenv("FLASHAPPLY_LOGO_PATH", ""),
        "app/flash_apply_logo.png",
        "flash_apply_logo.png",
        "assets/flashapply-logo.png",
        "assets/logo.png",
        "logo.png",
    ]
    for path in candidates:
        if path and Path(path).exists():
            return path
    return None


if "result" not in st.session_state:
    st.session_state["result"] = None
if "premium_unlocked" not in st.session_state:
    st.session_state["premium_unlocked"] = False
if "payment_url" not in st.session_state:
    st.session_state["payment_url"] = ""

if st.query_params.get("payment") == "success":
    st.session_state["premium_unlocked"] = True

_inject_styles()

left_col, right_col = st.columns([1.08, 1.0], gap="large")

with left_col:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero">'
        '<div class="hero-badge">Multi-Agent AI</div>'
        '<h1>FlashApply</h1>'
        '<p>Global AI Platform - CV Customizer Agents</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Votre CV actuel</p><p class="card-subtitle">PDF, DOCX, TXT ou image</p>', unsafe_allow_html=True)
    uploaded_cv = st.file_uploader("Chargez votre CV", type=["pdf", "docx", "txt", "png", "jpg", "jpeg"], label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Lien de l\'offre d\'emploi</p><p class="card-subtitle">LinkedIn, Welcome to the Jungle, Indeed, etc.</p>', unsafe_allow_html=True)
    offer_url = st.text_input("URL de l'offre", placeholder="https://www.linkedin.com/jobs/view/...", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Parametres de personnalisation</p><p class="card-subtitle">Adaptez le CV au pays cible</p>', unsafe_allow_html=True)
    c_country, c_contract = st.columns(2)
    with c_country:
        country = st.selectbox("Pays cible", get_available_countries())
    with c_contract:
        st.selectbox("Type de contrat", ["Emploi", "Stage", "Alternance"], index=0)

    has_llm_key = bool(os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY"))
    if has_llm_key:
        st.success("Cle API LLM detectee")
    else:
        st.warning("Pas de cle API LLM: mode fallback sans LLM")

    run = st.button("Lancer l'analyse", type="primary")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Paiement Stripe</p><p class="card-subtitle">Debloquez le PDF premium via Stripe Payment Link</p>', unsafe_allow_html=True)
    is_premium = st.session_state.get("premium_unlocked", False)
    if is_premium:
        st.success("Premium actif. Le telechargement PDF est debloque.")
    else:
        st.info("Premium non actif. Payez pour debloquer le telechargement PDF.")
        amount = st.selectbox("Plan", ["$5", "$10", "$20"], index=0)
        amount_map = {"$5": 500, "$10": 1000, "$20": 2000}
        if st.button("Generer un lien de paiement Stripe"):
            try:
                st.session_state["payment_url"] = create_payment_link(
                    amount_cents=amount_map[amount],
                    currency="usd",
                    product_name=f"FlashApply Premium {amount}",
                )
                st.success("Lien de paiement genere.")
            except Exception as exc:
                st.error(f"Erreur Stripe: {exc}")
        if st.session_state.get("payment_url"):
            st.link_button("Ouvrir la page de paiement", st.session_state["payment_url"])
            st.caption("Apres paiement, vous serez redirige vers l'app avec premium actif.")
    st.markdown("</div>", unsafe_allow_html=True)

    if run:
        if uploaded_cv is None:
            st.error("Veuillez uploader un CV.")
            st.stop()
        if not offer_url.strip():
            st.error("Veuillez fournir le lien de l'offre.")
            st.stop()

        suffix = os.path.splitext(uploaded_cv.name)[1] or ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_cv.getbuffer())
            tmp_path = tmp.name

        try:
            with st.spinner("Execution des agents..."):
                st.session_state["result"] = run_pipeline(
                    cv_file_path=tmp_path,
                    offer_url=offer_url.strip(),
                    country=country,
                )
        except Exception as exc:
            st.error(f"Erreur pendant le traitement: {exc}")
            st.stop()
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

with right_col:
    result = st.session_state.get("result")
    if not result:
        st.markdown('<div class="panel placeholder"><div class="star">✦</div><h3>Vos resultats apparaitront ici</h3><p>Remplissez le formulaire et lancez l\'analyse pour obtenir votre CV optimise et son score de matching.</p></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f'<div class="kpi"><div class="label">Match Original</div><div class="value">{result["original_matching"]["match_score"]}</div></div>', unsafe_allow_html=True)
        with k2:
            st.markdown(f'<div class="kpi"><div class="label">Match Custom</div><div class="value">{result["personalized_matching"]["match_score"]}</div></div>', unsafe_allow_html=True)
        with k3:
            st.markdown(f'<div class="kpi"><div class="label">Conformite</div><div class="value">{result["compliance"]["compliance_score"]}</div></div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("CV personnalise")
        st.markdown(result["personalized_cv"])

        country_rules = get_country_rules(result.get("country", "France"))
        if st.session_state.get("premium_unlocked"):
            pdf_bytes = build_pdf_from_text(result["personalized_cv"], country_rules)
            st.download_button(
                label="Telecharger le CV personnalise (.pdf)",
                data=pdf_bytes,
                file_name=f"cv_personnalise_{result.get('country', 'france').lower()}.pdf",
                mime="application/pdf",
            )
        else:
            st.warning("Telechargement PDF reserve au plan premium (paiement Stripe).")
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Details techniques"):
            st.json(result)
