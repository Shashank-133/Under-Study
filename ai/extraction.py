"""
Extract structured incident data from raw error text using Sarvam AI.

Input:
    raw_text: A string containing an error message, stack trace, or bug report
              pasted by a junior developer. May include file paths, line numbers,
              and informal description.

Output:
    dict matching the Understudy incident shape (without id/created_at — assigned at ingestion):

    {
        "title": str,
        "description": str,
        "error_signature": {
            "message": str,
            "stack_trace": str,
            "error_type": str,
        },
        "root_cause": {
            "category": str,       # e.g. "null_reference", "cors_misconfiguration"
            "description": str,
        },
        "files": [
            {"path": str, "line": int | None},
        ],
        "fix_pattern": {
            "description": str,
            "code_snippet": str,
        },
        "resolved_by": {
            "name": str,
            "email": str,
        },
        "pr": {
            "number": int,
            "url": str,
            "title": str,
        },
    }

Person 3: Sarvam API call implemented below.

--------------------------------------------------------------------------
HOW THIS WORKS (read this if you're new to the file)
--------------------------------------------------------------------------
1. We build a strict "extraction prompt" that tells Sarvam's chat model
   (sarvam-m) to read the raw error text and return ONLY a JSON object
   that matches the Understudy incident shape above.
2. We call Sarvam's OpenAI-compatible Chat Completions endpoint:
       POST https://api.sarvam.ai/v1/chat/completions
   using plain `requests` (no SDK needed — keeps the ai/ folder dependency
   footprint tiny, per hackathon time constraints).
3. Because LLMs sometimes wrap JSON in ```json fences or add stray text,
   `_extract_json_object()` defensively pulls out the first valid JSON
   object from the response before parsing.
4. If SARVAM_API_KEY is missing, or the API call fails for any reason
   (network, rate limit, bad response), we NEVER crash the pipeline —
   we fall back to the original lightweight stub so local dev / demos
   without a key still work end-to-end (this mirrors the original stub
   behavior that Person 2 / ingestion already depend on).
--------------------------------------------------------------------------
"""

import json
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

SARVAM_CHAT_URL = "https://api.sarvam.ai/v1/chat/completions"
SARVAM_MODEL = "sarvam-m"
REQUEST_TIMEOUT_SECONDS = 30

# The prompt is intentionally strict: one job (extraction), one output format
# (raw JSON, nothing else). This keeps parsing reliable and avoids the model
# adding conversational filler ("Sure, here's the JSON...") that would break
# json.loads().
EXTRACTION_PROMPT = """You are an expert software engineer helping build an internal \
"team memory" tool. You will be given a raw error message, stack trace, or informal \
bug report pasted by a junior developer. Extract structured incident data from it.

Return ONLY a single JSON object (no markdown fences, no commentary, no leading or \
trailing text) with EXACTLY this shape:

{{
  "title": "short human-readable title for this bug, <=80 chars",
  "description": "1-3 sentence plain-English description of what went wrong",
  "error_signature": {{
    "message": "the core error message, first line only",
    "stack_trace": "the full stack trace / traceback as given, or empty string if none",
    "error_type": "the exception/error class name, e.g. TypeError, CORS, ConnectionError"
  }},
  "root_cause": {{
    "category": "short snake_case category, e.g. null_reference, cors_misconfiguration, \
async_error_handling, configuration, unclassified",
    "description": "1-2 sentence explanation of the underlying cause, best guess if unclear"
  }},
  "files": [
    {{"path": "relative/file/path.ext", "line": 24}}
  ],
  "fix_pattern": {{
    "description": "short description of how this class of bug is typically fixed",
    "code_snippet": "a short illustrative code snippet, or empty string if none is obvious"
  }},
  "resolved_by": {{
    "name": "name if mentioned in the text, otherwise \\"Unknown\\"",
    "email": "email if mentioned, otherwise empty string"
  }},
  "pr": {{
    "number": 0,
    "url": "",
    "title": ""
  }}
}}

Rules:
- If information for a field is not present in the input, use a sensible empty \
default (empty string, empty list, or 0) rather than inventing facts.
- "files" should list every file path + line number you can find in the stack trace \
or text; use null for line if unknown. Return [] if none found.
- Keep "error_type" to a single short token when possible.
- Output MUST be valid JSON and MUST be parseable by json.loads() with nothing else \
around it.

Raw error text:
---
{raw_text}
---
"""


def _extract_json_object(text: str) -> str:
    """
    Pull the first top-level JSON object out of a model response.

    Models occasionally wrap JSON in ```json ... ``` fences or add a stray
    sentence before/after. Rather than trust the raw response, we look for
    the first '{' and the matching last '}' and hand that slice to json.loads().
    """
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return fenced.group(1)

    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace == -1 or last_brace == -1 or last_brace < first_brace:
        raise ValueError("No JSON object found in model response")

    return text[first_brace : last_brace + 1]


def _stub_result(raw_text: str) -> dict:
    """Original lightweight fallback — used when no API key or the call fails."""
    return {
        "title": "Extracted incident (stub)",
        "description": f"Auto-extracted from {len(raw_text)} characters of input.",
        "error_signature": {
            "message": raw_text.split("\n")[0][:200],
            "stack_trace": raw_text,
            "error_type": "Unknown",
        },
        "root_cause": {
            "category": "unclassified",
            "description": "Pending Sarvam extraction.",
        },
        "files": [],
        "fix_pattern": {
            "description": "Pending extraction.",
            "code_snippet": "",
        },
        "resolved_by": {
            "name": "Unknown",
            "email": "",
        },
        "pr": {
            "number": 0,
            "url": "",
            "title": "",
        },
    }


def _call_sarvam_chat(prompt: str, api_key: str) -> str:
    """
    Low-level call to Sarvam's OpenAI-compatible chat completions endpoint.
    Returns the raw text content of the model's reply.
    Raises on any HTTP or network error — caller is responsible for fallback.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": SARVAM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,  # low temperature: we want consistent, structured output
    }

    response = requests.post(
        SARVAM_CHAT_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT_SECONDS
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def extract_incident(raw_text: str) -> dict:
    """
    Extract a structured incident dict from raw error text.

    Uses Sarvam AI (sarvam-m chat model) when SARVAM_API_KEY is configured.
    Falls back to a deterministic stub when the key is missing or the API
    call fails, so the rest of the pipeline (backend, ingestion, demos)
    never breaks because of this module.
    """
    api_key = os.getenv("SARVAM_API_KEY")

    if not api_key:
        # Stub works without a key for local dev (unchanged behavior from before)
        return _stub_result(raw_text)

    try:
        prompt = EXTRACTION_PROMPT.format(raw_text=raw_text)
        raw_reply = _call_sarvam_chat(prompt, api_key)
        json_str = _extract_json_object(raw_reply)
        parsed = json.loads(json_str)

        # Defensive shape-check: make sure every top-level key the rest of the
        # app expects is present, even if Sarvam omitted one. This keeps the
        # return type stable for Person 2 (backend) and ingestion.py.
        expected_keys = [
            "title",
            "description",
            "error_signature",
            "root_cause",
            "files",
            "fix_pattern",
            "resolved_by",
            "pr",
        ]
        stub = _stub_result(raw_text)
        for key in expected_keys:
            parsed.setdefault(key, stub[key])

        return parsed

    except (requests.RequestException, ValueError, KeyError, json.JSONDecodeError) as exc:
        # Network issue, bad API response, or unparseable JSON — never crash
        # the caller. Fall back to the stub and keep a breadcrumb in the
        # description so it's obvious in logs/demo that Sarvam wasn't used.
        fallback = _stub_result(raw_text)
        fallback["description"] += f" (Sarvam extraction failed: {exc})"
        return fallback


if __name__ == "__main__":
    sample = """TypeError: Cannot read property 'map' of undefined
    at Dashboard.jsx:24
    at renderWithHooks"""
    print(json.dumps(extract_incident(sample), indent=2))
