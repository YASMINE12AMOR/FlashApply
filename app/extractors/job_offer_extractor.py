import requests


def fetch_job_offer(url: str) -> str:
    jina_url = f"https://r.jina.ai/{url}"
    response = requests.get(jina_url, timeout=30)
    response.raise_for_status()
    return response.text.strip()
