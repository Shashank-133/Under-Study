"""
Shared helpers to call Person 3 AI modules from backend / ingestion.
Loads repo-root .env and ignores placeholder keys.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
AI_ROOT = REPO_ROOT / "ai"

load_dotenv(REPO_ROOT / ".env")

_PLACEHOLDERS = {
    "",
    "your-sarvam-api-key",
    "your-neo4j-password",
    "your-render-api-key",
}


def env_value(name: str) -> str | None:
    value = (os.getenv(name) or "").strip()
    if not value or value in _PLACEHOLDERS:
        return None
    if "xxxxxxxx" in value:
        return None
    return value


def ensure_ai_path() -> None:
    if AI_ROOT.is_dir() and str(AI_ROOT) not in sys.path:
        sys.path.insert(0, str(AI_ROOT))


def extract_incident(raw_text: str) -> dict:
    ensure_ai_path()
    # Propagate cleaned key so ai modules see a real key or nothing
    key = env_value("SARVAM_API_KEY")
    if key:
        os.environ["SARVAM_API_KEY"] = key
    else:
        os.environ.pop("SARVAM_API_KEY", None)

    try:
        from extraction import extract_incident as _extract  # type: ignore

        return _extract(raw_text)
    except Exception:
        first_line = (raw_text or "").split("\n")[0][:200]
        return {
            "title": "Ingested incident",
            "description": f"Auto-extracted from {len(raw_text)} characters of input.",
            "error_signature": {
                "message": first_line,
                "stack_trace": raw_text,
                "error_type": "Unknown",
            },
            "root_cause": {
                "category": "unclassified",
                "description": "Pending extraction.",
            },
            "files": [],
            "fix_pattern": {
                "description": "Pending extraction.",
                "code_snippet": "",
            },
            "resolved_by": {"name": "Unknown", "email": ""},
            "pr": {"number": 0, "url": "", "title": ""},
        }


def generate_answer(graph_results: dict, language: str = "en") -> str:
    ensure_ai_path()
    key = env_value("SARVAM_API_KEY")
    if key:
        os.environ["SARVAM_API_KEY"] = key
    else:
        os.environ.pop("SARVAM_API_KEY", None)

    try:
        from answer_generation import generate_answer as _generate  # type: ignore

        return _generate(graph_results, language)
    except Exception:
        incidents = graph_results.get("similar_incidents") or []
        confidence = float(graph_results.get("confidence") or 0.0)
        ask_person = graph_results.get("ask_person")
        if not incidents:
            return (
                "I couldn't find a close match in your team's history yet. "
                "Try pasting the full stack trace, or ask a teammate to ingest this incident."
            )
        top = incidents[0]
        person_line = f" You might want to ask {ask_person}." if ask_person else ""
        answer = (
            f'Your team hit something like this before - "{top.get("title", "a similar issue")}" '
            f"(confidence: {confidence:.0%}). Suggested fix: "
            f"{top.get('fix_summary', 'see the linked PR')}.{person_line}"
        )
        if language in {"hi", "ta", "te"}:
            return f"[{language}] {answer}"
        return answer
