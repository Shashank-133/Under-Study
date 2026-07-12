# Person 3 (AI) — Work Log

Scope: `ai/` folder only, per `README.md` / `docs/ROLE_GUIDE.md` ownership rules.
No files outside `ai/` were touched.

## Summary

All four stub modules in `ai/` are now wired to real logic, each with a
safe fallback so the rest of the app (backend stub, frontend, ingestion)
never breaks if a Sarvam API key isn't set or an API call fails.

| File | Before | After |
|---|---|---|
| `extraction.py` | Returned a hardcoded placeholder dict | Calls Sarvam's chat completions API (`sarvam-m`) with a strict JSON-extraction prompt, parses + validates the response |
| `embeddings.py` | Jaccard token-overlap only | Uses `sentence-transformers` (`all-MiniLM-L6-v2`) + cosine similarity; falls back to the original token-overlap logic if the model can't load |
| `answer_generation.py` | Fixed string template | Calls Sarvam's chat completions API to write a natural, senior-dev-style paragraph from the graph results; falls back to the original template |
| `multilingual.py` | Returned `"[Stub — {lang}] {answer}"` | Calls Sarvam's Translate API for hi/ta/te, with a mask-and-restore step so code snippets/file paths are never translated or mangled |

Also added: `ai/requirements.txt` (dependencies scoped only to this folder)
and this log file.

---

## 1. `extraction.py`

**What it does now:** Sends the raw pasted error text to Sarvam's chat
model (`sarvam-m`) via `POST https://api.sarvam.ai/v1/chat/completions`,
using a prompt that forces the model to return a single JSON object
matching the exact incident shape the rest of the app expects
(`title`, `description`, `error_signature`, `root_cause`, `files`,
`fix_pattern`, `resolved_by`, `pr`).

**Key implementation details:**
- `_extract_json_object()` strips markdown code fences / stray text
  around the JSON before calling `json.loads()` — LLMs sometimes wrap
  JSON in ```` ```json ... ``` ````.
- After parsing, every expected top-level key is defensively filled in
  with the stub's default if the model happened to omit one, so
  downstream code (backend, ingestion) can always rely on the shape.
- **Fallback:** no API key → same stub as before. API call fails for any
  reason (network, bad JSON, rate limit) → falls back to the stub, with
  the failure reason appended to `description` for visibility in
  logs/demos, rather than raising an exception.

**Try it:**
```bash
cd ai
python extraction.py
```
Without `SARVAM_API_KEY` set, this prints the original stub-shaped JSON
(confirmed working — see test output below). With a real key in `.env`,
it will print a real extracted incident.

---

## 2. `embeddings.py`

**What it does now:** `compute_similarity(sig_a, sig_b)` encodes both
error signatures with a local `sentence-transformers` model
(`all-MiniLM-L6-v2`) and returns their cosine similarity, rescaled from
`[-1, 1]` to `[0, 1]` to match the score contract used everywhere else in
the app (`Field(ge=0.0, le=1.0)` on `SimilarIncidentRef.score` /
`SimilarIncidentResult.similarity_score`).

**Why a local model instead of a hosted Sarvam call:** `ROLE_GUIDE.md`
explicitly allows either "Sarvam embeddings or sentence-transformers".
Sarvam's public API surface is centered on chat/translation/speech, not a
dedicated embeddings endpoint, and this function sits on the hot path of
every `/query` request — a local model avoids extra network latency on
every single request during a live demo.

**Fallback:** if `sentence-transformers` isn't installed, or the model
weights can't be downloaded (e.g. sandboxed/offline environment), the
function transparently falls back to the original Jaccard token-overlap
logic. This was verified during testing — in this sandbox the model
download isn't reachable, and `compute_similarity()` correctly fell back
and still returned sensible scores.

**Try it:**
```bash
cd ai
pip install -r requirements.txt --break-system-packages
python embeddings.py
```

---

## 3. `answer_generation.py`

**What it does now:** `generate_answer(graph_results, language)` builds a
short prompt summarizing the top matched incident (title, fix summary,
confidence, who to ask) and asks Sarvam's chat model to phrase it as one
short, warm paragraph — like a quick message from a helpful senior
teammate, not a formal report. If `graph_results` has no similar
incidents at all, we skip the API call entirely (nothing to phrase) and
return the original "no match" message.

**Multilingual handoff:** when `language != "en"`, this module generates
the English answer first, then calls `multilingual.translate_answer()` to
translate it — keeping "what to say" (this file) and "how to say it in
another language" (`multilingual.py`) cleanly separated, as described in
`ROLE_GUIDE.md`.

**Fallback:** no API key, or the Sarvam call fails → falls back to the
original deterministic string template, so the function never raises.

**Try it:**
```bash
cd ai
python answer_generation.py
```

---

## 4. `multilingual.py`

**What it does now:** `translate_answer(answer, target_lang)` calls
Sarvam's Translate API (`POST https://api.sarvam.ai/translate`) to
translate an answer into Hindi, Tamil, or Telugu.

**Preserving code/technical terms (the tricky part):** A raw translation
call would risk the model "translating" or mangling things like
`` `data?.users ?? []` `` or `Dashboard.jsx:24`. To prevent that, the
module masks code-like spans before sending text to Sarvam, and restores
them after:
1. `_mask_code_spans()` finds backticked code (`` `like this` ``) and
   bare path/identifier-looking tokens (e.g. `Dashboard.jsx:24`,
   `data?.users ?? []`) and swaps each for a placeholder like
   `__CODE_0__`.
2. The now-code-free English text is sent to Sarvam for translation.
3. `_unmask_code_spans()` puts the original code back into the
   translated string, unchanged, in English.

**Fallback:** no API key → same `"[Stub — {Language}] {answer}"` behavior
as before. API call fails → same idea, with the failure reason included.

**Try it:**
```bash
cd ai
python multilingual.py
```

---

## Environment setup

Add your key to `.env` at the repo root (already listed in
`.env.example`, not changed by this work):

```
SARVAM_API_KEY=your-sarvam-api-key
```

Install the AI-folder-specific dependencies:

```bash
cd ai
pip install -r requirements.txt --break-system-packages
```

(`requests`, `python-dotenv`, `sentence-transformers`, `numpy` — these
don't touch or conflict with `backend/requirements.txt`.)

---

## What was verified

All four modules were run locally **without** a `SARVAM_API_KEY` set, to
confirm the no-key fallback path (which local dev / other teammates may
rely on) still works exactly as it did before:

- `extraction.py` → returns the original stub JSON shape ✅
- `embeddings.py` → falls back to token-overlap scoring when the local
  embedding model can't be downloaded (sandboxed/offline), returns
  sensible relative scores (related errors score higher than unrelated
  ones) ✅
- `answer_generation.py` → returns the original template string in
  English, and correctly hands off to `multilingual.py`'s stub for
  non-English languages ✅
- `multilingual.py` → returns the original `"[Stub — {Language}]"`
  prefixed string for hi/ta/te ✅

**Not verified against the live Sarvam API** in this environment (no
outbound network access to `api.sarvam.ai`, and no API key was provided).
Once `SARVAM_API_KEY` is set in a normal dev environment with internet
access, re-run each file directly (`python <file>.py`) to confirm the
real API path — the code is written defensively so a bad/missing key or
a failed call degrades to the stub behavior instead of crashing.

---

## Notes for Person 2 (backend) integration

- `extract_incident(raw_text) -> dict` — unchanged signature.
- `compute_similarity(sig_a, sig_b) -> float` — unchanged signature,
  0.0–1.0 range preserved.
- `generate_answer(graph_results, language="en") -> str` — unchanged
  signature. `graph_results` still expects `similar_incidents`,
  `confidence`, `ask_person` keys exactly as before.
- `translate_answer(answer, target_lang) -> str` — unchanged signature.

No function signatures changed, so `backend/` and `ingestion/` can import
and call these exactly as originally documented in `ROLE_GUIDE.md` —
nothing to coordinate on the calling side.

## Notes on API keys / cost

- Every Sarvam call is gated behind `os.getenv("SARVAM_API_KEY")` — if
  it's unset, no network call is attempted at all.
- All Sarvam calls have explicit timeouts (`REQUEST_TIMEOUT_SECONDS`) so a
  slow/hanging API can't hang the whole `/query` request indefinitely.
- `answer_generation.py` skips calling Sarvam entirely when there are no
  similar incidents to describe, avoiding an unnecessary API call.
