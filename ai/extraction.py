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

Person 3: Replace the placeholder return with a real Sarvam API call.
"""

import json
import os

from dotenv import load_dotenv

load_dotenv()


def extract_incident(raw_text: str) -> dict:
    api_key = os.getenv("SARVAM_API_KEY")

    # TODO: Call Sarvam AI with a structured extraction prompt.
    # Example (not implemented):
    #   response = sarvam_client.chat.completions.create(
    #       model="sarvam-m",
    #       messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(raw_text=raw_text)}],
    #   )
    #   return json.loads(response.choices[0].message.content)

    if not api_key:
        pass  # Stub works without a key for local dev

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


if __name__ == "__main__":
    sample = """TypeError: Cannot read property 'map' of undefined
    at Dashboard.jsx:24
    at renderWithHooks"""
    print(json.dumps(extract_incident(sample), indent=2))
