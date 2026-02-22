from langchain.tools import tool 
import mimetypes 
import docx 
import pytesseract 
from PIL import Image 
import pdfplumber 

@tool 
def extract_cv_text(file_path: str) -> str: 
    mime, _ = mimetypes.guess_type(file_path) 

    if mime == "application/pdf": 
        text = "" 
        with pdfplumber.open(file_path) as pdf: 
            for page in pdf.pages: 
                text += page.extract_text() + "\n" 
        return text 

    if mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document": 
        doc = docx.Document(file_path) 
        return "\n".join([p.text for p in doc.paragraphs]) 

    if mime and mime.startswith("image"): 
        img = Image.open(file_path) 
        return pytesseract.image_to_string(img) 

    if mime == "text/plain": 
        with open(file_path, "r", encoding="utf-8") as f: 
            return f.read() 

    return "Unsupported file format"
