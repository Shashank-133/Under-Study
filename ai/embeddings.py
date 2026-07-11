"""
Error signature similarity for matching new bugs to past incidents.

Person 3: Replace with real embeddings (Sarvam or sentence-transformers).
"""


def compute_similarity(sig_a: str, sig_b: str) -> float:
    """
    Return a score between 0.0 and 1.0 indicating how similar two error signatures are.
    Stub uses token overlap; replace with vector cosine similarity.
    """
    if not sig_a or not sig_b:
        return 0.0

    tokens_a = set(sig_a.lower().split())
    tokens_b = set(sig_b.lower().split())

    if not tokens_a or not tokens_b:
        return 0.0

    overlap = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return round(overlap / union, 4) if union else 0.0
