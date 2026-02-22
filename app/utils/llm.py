import os

from dotenv import load_dotenv

load_dotenv()


def get_llm():
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    from langchain_openai import ChatOpenAI

    model = os.getenv("DEEPSEEK_MODEL") or os.getenv("OPENAI_MODEL") or "deepseek-reasoner"
    base_url = (
        os.getenv("DEEPSEEK_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or "https://api.deepseek.com"
    )
    if base_url:
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.2,
        )
    return ChatOpenAI(model=model, api_key=api_key, temperature=0.2)
