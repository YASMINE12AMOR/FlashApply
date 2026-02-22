from __future__ import annotations

import os

DEFAULT_DEEPSEEK_MODEL = "deepseek-reasoner"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"


def resolve_deepseek_api_key(
    override: str | None = None,
    saved_key: str | None = None,
) -> str:
    if override and override.strip():
        return override.strip()
    if saved_key and saved_key.strip():
        return saved_key.strip()
    return os.getenv("DEEPSEEK_API_KEY", "").strip()
