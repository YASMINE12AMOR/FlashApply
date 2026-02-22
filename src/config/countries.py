from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_country_rules() -> dict[str, dict[str, Any]]:
    data_dir = Path(__file__).resolve().parent.parent / "data" / "countries"
    rules: dict[str, dict[str, Any]] = {}
    for file_path in sorted(data_dir.glob("*.json")):
        with file_path.open("r", encoding="utf-8-sig") as f:
            payload = json.load(f)
        country_name = (payload.get("country") or "").strip()
        if country_name:
            rules[country_name] = payload
    return rules


COUNTRY_RULES = _load_country_rules()
