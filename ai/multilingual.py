"""
Translate answers to Hindi, Tamil, or Telugu while keeping code/technical terms intact.

Person 3: Real Sarvam multilingual API implemented below.

--------------------------------------------------------------------------
HOW THIS WORKS (read this if you're new to the file)
--------------------------------------------------------------------------
We call Sarvam AI's Translate API:
    POST https://api.sarvam.ai/translate

Sarvam's translation model is good at natural prose, but a debugging answer
usually has file paths, variable names, and code snippets mixed into the
English sentence (e.g. "Guard with `data?.users ?? []` in Dashboard.jsx:24").
If we translate that whole string as-is, the model may "helpfully" mangle
the code or transliterate identifiers — which would break the answer for a
developer trying to copy-paste the fix.

To prevent that, we use a mask-and-restore strategy:
  1. `_mask_code_spans()` finds anything that looks like code or a path —
     backticked spans (`like this`), and bare file-path-looking tokens
     (contains a "/" or ends in a common code extension) — and replaces
     each with a unique placeholder token (e.g. "__CODE_0__").
  2. We send the now-code-free English text to Sarvam's Translate API.
  3. `_unmask_code_spans()` puts the original code/paths back into the
     translated string, unchanged.

This means: prose gets translated into fluent Hindi/Tamil/Telugu, while
`data?.users ?? []`, `Dashboard.jsx:24`, function names, etc. stay exactly
as an English developer would type them — which is the explicit
requirement in ROLE_GUIDE.md ("Keep code snippets, file paths, and
identifiers in English").

Fallback: if SARVAM_API_KEY is missing or the API call fails, we fall back
to the original stub behavior (prefixed placeholder string) so callers
never crash.
--------------------------------------------------------------------------
"""

import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
load_dotenv()

SARVAM_TRANSLATE_URL = "https://api.sarvam.ai/translate"
REQUEST_TIMEOUT_SECONDS = 20

SUPPORTED_LANGUAGES = {"hi": "Hindi", "ta": "Tamil", "te": "Telugu"}

# Sarvam's translate API expects BCP-47-style codes like "hi-IN".
_SARVAM_LANGUAGE_CODES = {
    "hi": "hi-IN",
    "ta": "ta-IN",
    "te": "te-IN",
}

# Matches backticked code spans (`like this`) or bare tokens that look like
# file paths / identifiers (contain a slash, a dot-extension, or ::/->/()).
_CODE_SPAN_PATTERN = re.compile(
    r"`[^`]+`"                              # `backticked code`
    r"|\b[\w./-]+\.(?:jsx?|tsx?|py|json|css|md)(?::\d+)?\b"  # path.ext or path.ext:line
    r"|\b\w+\([^)]*\)\??\s*\?\?\s*[^\s.,;]+"  # e.g. data?.users ?? []
)


def _mask_code_spans(text: str) -> tuple[str, dict[str, str]]:
    """
    Replace code-like spans with placeholder tokens before translation.
    Returns (masked_text, mapping_of_placeholder_to_original).
    """
    mapping: dict[str, str] = {}

    def _replace(match: re.Match) -> str:
        placeholder = f"__CODE_{len(mapping)}__"
        mapping[placeholder] = match.group(0)
        return placeholder

    masked_text = _CODE_SPAN_PATTERN.sub(_replace, text)
    return masked_text, mapping


def _unmask_code_spans(text: str, mapping: dict[str, str]) -> str:
    """Restore original code/paths into the translated string."""
    for placeholder, original in mapping.items():
        text = text.replace(placeholder, original)
    return text


def _call_sarvam_translate(text: str, target_lang: str, api_key: str) -> str:
    """
    Low-level call to Sarvam's Translate API.
    Raises on any HTTP/network error — caller is responsible for fallback.
    """
    headers = {
        "api-subscription-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "input": text,
        "source_language_code": "en-IN",
        "target_language_code": _SARVAM_LANGUAGE_CODES[target_lang],
        "mode": "modern-colloquial",
        "output_script": None,
        "numerals_format": "international",
    }

    response = requests.post(
        SARVAM_TRANSLATE_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT_SECONDS
    )
    response.raise_for_status()
    data = response.json()
    return data["translated_text"]


def translate_answer(answer: str, target_lang: str) -> str:
    """
    Translate a generated answer into Hindi, Tamil, or Telugu, preserving
    code snippets, file paths, and identifiers in English.

    Falls back to the original English answer (English/unsupported languages)
    or a stub-prefixed string (Sarvam call fails / no API key) so callers
    never crash.
    """
    if target_lang == "en":
        return answer

    if target_lang not in SUPPORTED_LANGUAGES:
        return answer

    api_key = os.getenv("SARVAM_API_KEY")
    lang_name = SUPPORTED_LANGUAGES[target_lang]

    if not api_key:
        # Stub works without a key for local dev (unchanged behavior from before)
        return f"[Stub — {lang_name}] {answer}"

    try:
        masked_text, code_map = _mask_code_spans(answer)
        translated_masked = _call_sarvam_translate(masked_text, target_lang, api_key)
        return _unmask_code_spans(translated_masked, code_map)

    except (requests.RequestException, KeyError, ValueError) as exc:
        # Never break the caller on a translation failure — fall back to a
        # clearly-labeled stub so it's obvious in the UI/logs that Sarvam
        # translation didn't run.
        return f"[Stub — {lang_name}, Sarvam translation failed: {exc}] {answer}"


if __name__ == "__main__":
    sample_answer = (
        "Your team hit something like this before — guard with "
        "`data?.users ?? []` in Dashboard.jsx:24."
    )
    for code in ("hi", "ta", "te"):
        print(f"--- {SUPPORTED_LANGUAGES[code]} ---")
        print(translate_answer(sample_answer, code))
        print()
