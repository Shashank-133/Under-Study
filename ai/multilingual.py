"""
Translate answers to Hindi, Tamil, or Telugu while keeping code/technical terms intact.

Person 3: Replace stub with Sarvam multilingual API.
"""

SUPPORTED_LANGUAGES = {"hi": "Hindi", "ta": "Tamil", "te": "Telugu"}


def translate_answer(answer: str, target_lang: str) -> str:
    if target_lang == "en":
        return answer

    if target_lang not in SUPPORTED_LANGUAGES:
        return answer

    # TODO: Call Sarvam translation with instruction to preserve code blocks and identifiers.
    lang_name = SUPPORTED_LANGUAGES[target_lang]
    return f"[Stub — {lang_name}] {answer}"
