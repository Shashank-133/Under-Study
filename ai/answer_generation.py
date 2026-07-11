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

Person 3: Wire to Sarvam for conversational tone; call multilingual.translate_answer
         when language != "en".
"""


def generate_answer(graph_results: dict, language: str = "en") -> str:
    incidents = graph_results.get("similar_incidents", [])
    confidence = graph_results.get("confidence", 0.0)
    ask_person = graph_results.get("ask_person")

    if not incidents:
        return (
            "[Stub] I couldn't find a close match in your team's history yet. "
            "Try pasting the full stack trace, or ask a teammate to ingest this incident."
        )

    top = incidents[0]
    title = top.get("title", "a similar issue")
    fix = top.get("fix_summary", "see the linked PR")
    person_line = f" You might want to ask {ask_person}." if ask_person else ""

    answer = (
        f"Your team hit something like this before — \"{title}\" "
        f"(confidence: {confidence:.0%}). Suggested fix: {fix}.{person_line}"
    )

    if language != "en":
        from multilingual import translate_answer

        return translate_answer(answer, language)

    return answer
