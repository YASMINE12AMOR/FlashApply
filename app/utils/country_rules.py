import json
from pathlib import Path


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "cv_customizer_agent.json"


def _load_profiles() -> dict:
    raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return raw["cv_customizer_agent"]["countries"]


def get_available_countries() -> list[str]:
    return list(_load_profiles().keys())


def _extract_forbidden_fields(personal_info: dict) -> list[str]:
    out = []
    for key, rule in personal_info.items():
        if isinstance(rule, dict) and rule.get("allowed") is False:
            out.append(key)
    return out


def _extract_personal_fields(personal_info: dict) -> list[str]:
    out = []
    for key, rule in personal_info.items():
        if isinstance(rule, dict) and (rule.get("required") or rule.get("recommended")):
            out.append(key)
    return out


def get_country_rules(country: str) -> dict:
    profiles = _load_profiles()

    selected_name = None
    for name in profiles:
        if name.lower() == (country or "").strip().lower():
            selected_name = name
            break
    if not selected_name:
        selected_name = "France"

    profile = profiles[selected_name]
    meta = profile.get("meta", {})
    fmt = profile.get("format", {})
    personal = profile.get("personal_information", {})
    sections = profile.get("sections", {})
    tone = profile.get("tone", {})

    return {
        "country": selected_name,
        "profile": profile,
        "document_name": meta.get("document_name", "CV"),
        "language": meta.get("language", ""),
        "length": fmt.get("length", {}).get("rule", ""),
        "min_pages": fmt.get("length", {}).get("min_pages"),
        "max_pages": fmt.get("length", {}).get("max_pages"),
        "layout": {
            "structure": fmt.get("layout", "single_column"),
            "design_pattern": profile.get("design_pattern", {}),
            "sidebar_layout": profile.get("sidebar_layout", {}),
            "header_layout": profile.get("header_layout", {}),
        },
        "photo": bool(personal.get("photo", {}).get("allowed", False) or personal.get("photo", {}).get("required", False)),
        "personal_info": _extract_personal_fields(personal),
        "forbidden_fields": _extract_forbidden_fields(personal),
        "section_order": sections.get("order", []),
        "tone": tone.get("style", ""),
        "cover_letter": profile.get("cover_letter", {}).get("name")
        or ("required" if profile.get("cover_letter", {}).get("required") else "recommended"),
        "key_rule": "; ".join(profile.get("cultural_notes", [])[:2]),
    }
