"""
Error signature similarity for matching new bugs to past incidents.

Person 3: Real embeddings implemented below.

--------------------------------------------------------------------------
HOW THIS WORKS (read this if you're new to the file)
--------------------------------------------------------------------------
Person 2 (backend) calls `compute_similarity(sig_a, sig_b)` to rank past
incidents against a new error signature when building the /query response.

We use `sentence-transformers` (a local, free, open-source embedding model)
rather than a hosted Sarvam embeddings call, for two reasons:

  1. As of writing, Sarvam AI's public API surface is focused on chat,
     translation, and speech — not a dedicated text-embeddings endpoint.
     ROLE_GUIDE.md explicitly allows either "Sarvam embeddings or
     sentence-transformers", so we picked the option that's stable and
     doesn't depend on a hosted endpoint being available/reliable.
  2. Similarity search is called on every /query request. Running a small
     local model avoids extra network latency + API cost on the hot path,
     which matters for a live demo.

Model used: "all-MiniLM-L6-v2" — a small (~80MB), fast, well-regarded
sentence-embedding model. It's downloaded once and cached locally by
sentence-transformers the first time this module runs.

Similarity metric: cosine similarity between the two embedding vectors,
mapped from [-1, 1] to [0, 1] so it matches the score contract used
elsewhere in the app (SimilarIncidentRef.score, similarity_score, etc.
are all Field(ge=0.0, le=1.0)).

Fallback: if sentence-transformers (or its model download) isn't
available in the current environment — e.g. no internet access, or the
package isn't installed yet — we fall back to the original Jaccard
token-overlap stub so the rest of the app keeps working.
--------------------------------------------------------------------------
"""

from functools import lru_cache

_MODEL_NAME = "all-MiniLM-L6-v2"


def _token_overlap_similarity(sig_a: str, sig_b: str) -> float:
    """Original stub logic — kept as a safe fallback (no dependencies required)."""
    if not sig_a or not sig_b:
        return 0.0

    tokens_a = set(sig_a.lower().split())
    tokens_b = set(sig_b.lower().split())

    if not tokens_a or not tokens_b:
        return 0.0

    overlap = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return round(overlap / union, 4) if union else 0.0


@lru_cache(maxsize=1)
def _get_model():
    """
    Lazily load the sentence-transformers model once per process and cache it.
    Returns None if the library/model can't be loaded (e.g. offline sandbox),
    which signals callers to fall back to token-overlap similarity.
    """
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(_MODEL_NAME)
    except Exception:
        # Any failure here (missing package, no internet to download weights,
        # etc.) should degrade gracefully rather than crash the API.
        return None


def compute_similarity(sig_a: str, sig_b: str) -> float:
    """
    Return a score between 0.0 and 1.0 indicating how similar two error
    signatures are.

    Uses sentence-transformer embeddings + cosine similarity when available;
    falls back to Jaccard token overlap otherwise (e.g. no internet access
    to download the model weights on first run).
    """
    if not sig_a or not sig_b:
        return 0.0

    model = _get_model()
    if model is None:
        return _token_overlap_similarity(sig_a, sig_b)

    import numpy as np

    embeddings = model.encode([sig_a, sig_b])
    vec_a, vec_b = embeddings[0], embeddings[1]

    denom = np.linalg.norm(vec_a) * np.linalg.norm(vec_b)
    if denom == 0:
        return 0.0

    cosine = float(np.dot(vec_a, vec_b) / denom)  # range roughly [-1, 1]
    normalized = (cosine + 1) / 2  # map to [0, 1] to match the score contract
    return round(max(0.0, min(1.0, normalized)), 4)


if __name__ == "__main__":
    a = "TypeError: Cannot read property 'map' of undefined at Dashboard.jsx:24"
    b = "TypeError: Cannot read properties of undefined (reading 'avatar') at ProfilePage.jsx:41"
    c = "Access to fetch blocked by CORS policy at authService.js:18"

    print(f"similar errors (both null-reference TypeErrors): {compute_similarity(a, b)}")
    print(f"unrelated errors (TypeError vs CORS):            {compute_similarity(a, c)}")
