import os
import re
import tempfile
from html import escape
from io import BytesIO

import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.agents.pipeline_agent import run_pipeline
from app.utils.country_rules import DEFAULT_COUNTRY_RULES


st.set_page_config(page_title="FlashApply", page_icon=":briefcase:", layout="wide")


def build_pdf_from_text(text: str) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        spaceAfter=6,
    )
    h1_style = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        spaceAfter=10,
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        spaceBefore=6,
        spaceAfter=8,
    )

    def format_inline(md_line: str) -> str:
        safe = escape(md_line)
        safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
        safe = re.sub(r"\*(.+?)\*", r"<i>\1</i>", safe)
        return safe

    story = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            story.append(Spacer(1, 8))
            continue

        stripped = line.lstrip()
        if stripped.startswith("# "):
            story.append(Paragraph(format_inline(stripped[2:].strip()), h1_style))
            continue
        if stripped.startswith("## "):
            story.append(Paragraph(format_inline(stripped[3:].strip()), h2_style))
            continue
        if stripped.startswith("### "):
            story.append(Paragraph(format_inline(stripped[4:].strip()), h2_style))
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            story.append(Paragraph(format_inline(stripped[2:].strip()), body_style, bulletText="•"))
            continue

        story.append(Paragraph(format_inline(stripped), body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

st.title("FlashApply - CV Agent App")
st.caption("CV + URL offre + pays -> CV personnalise + scores de matching")

with st.sidebar:
    st.subheader("Configuration")
    st.write("Pays cible")
    country = st.selectbox("Country", list(DEFAULT_COUNTRY_RULES.keys()), label_visibility="collapsed")
    has_llm_key = bool(os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY"))
    if has_llm_key:
        st.success("Cle API LLM detectee")
    else:
        st.warning("Pas de cle API LLM: mode fallback sans LLM")

st.subheader("Inputs")
uploaded_cv = st.file_uploader("Uploadez votre CV", type=["pdf", "docx", "txt", "png", "jpg", "jpeg"])
offer_url = st.text_input("Lien de l'offre (emploi/stage/alternance)")

if st.button("Lancer les agents", type="primary"):
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
        with st.spinner("Execution du pipeline agents..."):
            result = run_pipeline(cv_file_path=tmp_path, offer_url=offer_url.strip(), country=country)
    except Exception as exc:
        st.error(f"Erreur pendant le traitement: {exc}")
        st.stop()
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    st.subheader("Scores")
    c1, c2, c3 = st.columns(3)
    c1.metric("Score CV original vs Offre", f"{result['original_matching']['match_score']}/100")
    c2.metric("Score CV personnalise vs Offre", f"{result['personalized_matching']['match_score']}/100")
    c3.metric("Score conformite pays", f"{result['compliance']['compliance_score']}/100")

    st.subheader("Matching details")
    left, right = st.columns(2)
    left.write("Mots-cles presents (CV original)")
    left.write(result["original_matching"]["keywords_present"])
    right.write("Mots-cles manquants (CV original)")
    right.write(result["original_matching"]["keywords_missing"])

    st.subheader("CV personnalise (markdown)")
    st.markdown(result["personalized_cv"])

    pdf_bytes = build_pdf_from_text(result["personalized_cv"])
    st.download_button(
        label="Telecharger le CV personnalise (.pdf)",
        data=pdf_bytes,
        file_name="cv_personnalise.pdf",
        mime="application/pdf",
    )

    with st.expander("Voir les donnees brutes"):
        st.json(result)
