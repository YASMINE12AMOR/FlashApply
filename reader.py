from langchain.tools import tool 
from langchain_openai import ChatOpenAI
import requests
import mimetypes 
import docx 
import pytesseract 
from PIL import Image 
import pdfplumber 
@tool 
def extract_cv_text(file_path: str) -> str: 
    """ Extracts text from a CV in PDF, DOCX, image, or text format. """ 
    mime, _ = mimetypes.guess_type(file_path) 
    # PDF 
    if mime == "application/pdf": 
        text = "" 
        with pdfplumber.open(file_path) as pdf: 
            for page in pdf.pages: 
                text += page.extract_text() + "\n" 
        return text 
    # DOCX 
    if mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document": 
        doc = docx.Document(file_path) 
        return "\n".join([p.text for p in doc.paragraphs]) 
    # Images (JPG, PNG) 
    if mime and mime.startswith("image"): 
        img = Image.open(file_path) 
        return pytesseract.image_to_string(img) 
    # Text files 
    if mime == "text/plain": 
        with open(file_path, "r", encoding="utf-8") as f: 
            return f.read() 
    return "Unsupported file format"

@tool
def fetch_job_offer(url: str) -> str:
    """
    Fetches a clean text version of a job offer using Jina Reader.
    """
    jina_url = f"https://r.jina.ai/{url}"
    response = requests.get(jina_url)
    return response.text


llm = ChatOpenAI(model="gpt-4o-mini") 
@tool 
def match_cv_to_job(cv_text: str, job_text: str) -> str: 
    """ Compare a CV with a job offer and return a match score + analysis. """ 
    prompt = f""" You are an expert ATS system. Compare the following CV and job offer. Return a JSON with: - match_score (0-100) - strengths - missing_skills - recommendations CV: {cv_text} Job Offer: {job_text} """ 
    response = llm.invoke(prompt) 
    return response.content


