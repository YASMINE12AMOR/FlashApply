from __future__ import annotations

import os

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


def resolve_openai_api_key(override: str | None = None) -> str:
    if override and override.strip():
        return override.strip()
    return os.getenv("OPENAI_API_KEY", "").strip()
