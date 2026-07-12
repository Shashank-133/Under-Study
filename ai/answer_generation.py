"""
Generate a natural conversational answer from graph traversal results.

Input:
    graph_results: dict with keys like:
        - similar_incidents: list of matched incidents from Neo4j
        - confidence: float
        - ask_person: str | None

    language: "en" | "hi" | "ta" | "te" (default "en")

Output:
    str — human-readable answer for the junior developer.

Person 3: Wired to Sarvam for conversational tone; calls multilingual.translate_answer
         when language != "en".

--------------------------------------------------------------------------
HOW THIS WORKS (read this if you're new to the file)
--------------------------------------------------------------------------
Person 2's backend (or ingestion pipeline) runs graph traversal + similarity
scoring, then calls `generate_answer(graph_results, language)` to turn that
raw data into a friendly paragraph a junior dev would actually want to read.

We build a short prompt describing the top matches and ask Sarvam's chat
model (sarvam-m) to write ONE short, encouraging, plain-English paragraph —
the kind of thing a senior teammate would type in Slack, not a formal report.

Design choices:
  - We keep the prompt input strictly to what's already in graph_results
    (titles, fix summaries, confidence, who to ask) — we do NOT invent facts,
    we just ask the model to phrase them naturally.
  - If there are no similar incidents at all, we skip the API call entirely
    (nothing useful to phrase) and return the original "no match" message —
    saves an API call and avoids the model hallucinating a fix that doesn't
    exist.
  - Multilingual: when `language != "en"`, we first generate the answer in
    English, then hand it to `multilingual.translate_answer()`, which uses
    Sarvam's Translate API and preserves code/paths (see multilingual.py).
    This keeps the "generate meaning, then translate" responsibilities
    cleanly separated between the two modules, as ROLE_GUIDE.md describes.
  - Fallback: if SARVAM_API_KEY is missing or the API call fails, we fall
    back to the original deterministic template so callers never crash and
    local dev/demos without a key still work.
--------------------------------------------------------------------------
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
load_dotenv()

SARVAM_CHAT_URL = "https://api.sarvam.ai/v1/chat/completions"
SARVAM_MODEL = "sarvam-m"
REQUEST_TIMEOUT_SECONDS = 30

ANSWER_PROMPT = """You are a friendly, experienced senior developer helping a junior \
teammate who just pasted an error into an internal bug-memory tool. The tool already \
found the most relevant past incident(s) from the team's history using a graph \
database — your only job is to phrase the result naturally, like a quick Slack \
message from a helpful senior dev. Do not invent any facts not given below.

Top matching past incident: "{title}"
Suggested fix: {fix}
Confidence the tool has in this match: {confidence:.0%}
{ask_person_line}

Write ONE short paragraph (2-4 sentences) for the junior developer:
- Start by reassuring them the team has seen something similar before.
- Mention the fix in plain English (you may reference the exact fix text given).
- If a person to ask is given, naturally suggest reaching out to them.
- Keep it warm, concise, and free of markdown formatting or bullet points.
- Do not add a greeting like "Hi" or a sign-off.

Return ONLY the paragraph text, nothing else.
"""


def _no_match_message() -> str:
    """Fallback message when the graph has no similar incidents at all."""
    return (
        "I couldn't find a close match in your team's history yet. "
        "Try pasting the full stack trace, or ask a teammate to ingest this incident."
    )


def _template_answer(top: dict, confidence: float, ask_person: str | None) -> str:
    """Original deterministic template — used as a safe fallback."""
    title = top.get("title", "a similar issue")
    fix = top.get("fix_summary", "see the linked PR")
    person_line = f" You might want to ask {ask_person}." if ask_person else ""

    return (
        f'Your team hit something like this before — "{title}" '
        f"(confidence: {confidence:.0%}). Suggested fix: {fix}.{person_line}"
    )


def _call_sarvam_chat(prompt: str, api_key: str) -> str:
    """Low-level call to Sarvam's chat completions endpoint. Raises on failure."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": SARVAM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.6,  # a bit of warmth/variation is fine for conversational tone
    }

    response = requests.post(
        SARVAM_CHAT_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT_SECONDS
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def _generate_english_answer(graph_results: dict) -> str:
    """
    Build the English-language answer from graph_results, using Sarvam when
    available and falling back to the deterministic template otherwise.
    """
    incidents = graph_results.get("similar_incidents", [])
    confidence = graph_results.get("confidence", 0.0)
    ask_person = graph_results.get("ask_person")

    if not incidents:
        return _no_match_message()

    top = incidents[0]
    api_key = os.getenv("SARVAM_API_KEY")

    if not api_key:
        return _template_answer(top, confidence, ask_person)

    try:
        ask_person_line = f"Person to ask if more help is needed: {ask_person}" if ask_person else ""
        prompt = ANSWER_PROMPT.format(
            title=top.get("title", "a similar issue"),
            fix=top.get("fix_summary", "see the linked PR"),
            confidence=confidence,
            ask_person_line=ask_person_line,
        )
        return _call_sarvam_chat(prompt, api_key)

    except (requests.RequestException, KeyError, ValueError):
        # Never break the caller — fall back to the deterministic template.
        return _template_answer(top, confidence, ask_person)


def generate_answer(graph_results: dict, language: str = "en") -> str:
    """
    Generate a natural conversational answer from graph traversal results,
    translated into the requested language when needed.
    """
    english_answer = _generate_english_answer(graph_results)

    if language != "en":
        from multilingual import translate_answer

        return translate_answer(english_answer, language)

    return english_answer


if __name__ == "__main__":
    sample_graph_results = {
        "similar_incidents": [
            {
                "id": "inc-001",
                "title": "Null user list crashes dashboard",
                "similarity_score": 0.85,
                "fix_summary": "Guard with optional chaining: data?.users ?? []",
                "resolved_by": "Alice Kumar",
                "pr_url": "https://github.com/team/understudy/pull/142",
            }
        ],
        "confidence": 0.85,
        "ask_person": "Alice Kumar",
    }

    print("English:")
    print(generate_answer(sample_graph_results, "en"))
    print()
    print("Hindi:")
    print(generate_answer(sample_graph_results, "hi"))
