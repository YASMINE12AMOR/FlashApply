from langchain.tools import tool
import requests

@tool
def fetch_job_offer(url: str) -> str:
    jina_url = f"https://r.jina.ai/{url}"
    response = requests.get(jina_url)
    return response.text
