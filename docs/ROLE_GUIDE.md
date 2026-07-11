# Understudy — Role Guide (paste into your IDE)

Use this file as full context for your role. Copy the section for **your person number** into Cursor (or your AI assistant) at the start of your branch work.

**Repo:** Understudy — AI pair-debugger with institutional memory  
**Tracks:** Neo4j AuraDB · Sarvam AI · Render Workflows  
**Team:** 3 people, 3 branches — strict folder ownership

---

## Shared context (everyone reads this)

### What Understudy does
When a junior developer pastes an error, Understudy searches the team's past incidents in a Neo4j graph and returns:
- A conversational answer ("your team saw this before")
- Similar past bugs with fix summaries
- Who fixed it and which PR to look at
- A confidence score

### Folder ownership — do not cross lines

| Folder | Owner | You may NOT edit |
|--------|-------|------------------|
| `frontend/` | **Person 1** | `backend/`, `ai/` |
| `backend/` | **Person 2** | `frontend/`, `ai/` |
| `ai/` | **Person 3** | `frontend/`, `backend/` |
| `ingestion/` | **Team** — sync first | touches backend + ai |
| `.env.example`, API contract | **Team** — sync first | — |

### Current structure (after skeleton setup)

```
understudy/
├── README.md
├── .env.example
├── .gitignore
│
├── frontend/                 # Person 1 ONLY
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx           # working chat UI → POST /query
│       ├── App.css
│       ├── main.jsx
│       ├── components/       # you build here
│       └── pages/            # you build here
│
├── backend/                  # Person 2 ONLY
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py           # FastAPI, stub /query
│   │   ├── api/query.py      # frozen request/response models
│   │   ├── graph/connection.py
│   │   └── models/incident.py
│   └── seed_data/
│       └── incidents.json    # 4 example incidents
│
├── ai/                       # Person 3 ONLY
│   ├── extraction.py
│   ├── answer_generation.py
│   ├── multilingual.py
│   └── embeddings.py
│
├── ingestion/                # shared — team sync
│   └── ingest_job.py
│
└── docs/
    ├── PROGRESS.md
    └── ROLE_GUIDE.md         # this file
```

### Structure after everyone finishes (target)

```
understudy/
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── ChatInput.jsx
│       │   ├── ChatResponse.jsx
│       │   ├── LanguageToggle.jsx
│       │   ├── SimilarIncidentsList.jsx
│       │   └── ConfidenceBar.jsx
│       ├── pages/
│       │   ├── HomePage.jsx          # main chat
│       │   └── IngestionDemoPage.jsx # live ingestion demo
│       └── App.jsx                   # router between pages
│
├── backend/
│   └── app/
│       ├── graph/
│       │   ├── connection.py         # real AuraDB driver
│       │   ├── seed.py               # load 15-20 incidents
│       │   ├── queries.py            # Cypher traversal
│       │   └── similarity.py         # confidence scoring
│       └── main.py                   # real /query pipeline
│
├── ai/
│   ├── extraction.py                 # real Sarvam extraction
│   ├── answer_generation.py          # conversational answers
│   ├── multilingual.py               # hi/ta/te translation
│   └── embeddings.py                 # vector similarity
│
└── ingestion/
    └── ingest_job.py                 # Render cron → extract → Neo4j
```

### Frozen API contract — `POST /query`

**Do not change field names without updating frontend + backend in the same commit.**

Request:
```json
{ "error": "string", "language": "en|hi|ta|te" }
```

Response:
```json
{
  "answer": "string",
  "confidence": 0.72,
  "similar_incidents": [
    {
      "id": "inc-001",
      "title": "...",
      "similarity_score": 0.85,
      "fix_summary": "...",
      "resolved_by": "Alice Kumar",
      "pr_url": "https://..."
    }
  ],
  "ask_person": "Alice Kumar"
}
```

### How to run your part

- **Person 1:** `cd frontend && npm install && npm run dev` → http://localhost:5173
- **Person 2:** `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000`
- **Person 3:** `cd ai && python extraction.py` (test stubs); set `SARVAM_API_KEY` in `.env` for real API

---

# Person 1 — Frontend (3 phases)

**Your folder:** `frontend/` only  
**Your goal:** A polished chat app that talks to the backend and demos live ingestion.

---

## Phase 1 — Componentize the chat UI

**Status:** Starter `App.jsx` works; you make it production-ready.

**Create:**
- `src/components/ChatInput.jsx` — textarea + submit, loading state
- `src/components/ChatResponse.jsx` — renders answer, errors, empty state
- `src/components/SimilarIncidentsList.jsx` — list of past matches with PR links
- `src/components/ConfidenceBar.jsx` — visual confidence meter
- `src/pages/HomePage.jsx` — composes the above into the main screen
- Refactor `App.jsx` to use `HomePage` (or add React Router if you prefer)

**Wire to:**
- `POST /query` with body `{ error, language }` — already working in stub `App.jsx`
- Use `import.meta.env.VITE_API_URL` or Vite proxy (empty string = proxy in dev)

**Done when:**
- UI is split into reusable components
- Error handling shows friendly message if backend is down
- Layout looks demo-ready (spacing, typography, mobile-friendly)

---

## Phase 2 — Language toggle & response display

**Create:**
- `src/components/LanguageToggle.jsx` — English / Hindi / Tamil / Telugu selector
- Pass selected `language` in every `/query` request
- Style multilingual responses (RTL not needed; keep code snippets in monospace)

**Behavior:**
- Language preference persists in `localStorage` optional
- When backend returns stub, language field is sent but answer may still be English until Person 3 wires Sarvam — UI must still work

**Done when:**
- User can switch language before submitting
- Response panel clearly shows answer + confidence + ask_person + similar incidents
- No changes to `backend/` or `ai/`

---

## Phase 3 — Live ingestion demo page

**Create:**
- `src/pages/IngestionDemoPage.jsx` — second screen in the app
- Simple nav in `App.jsx` between **Chat** and **Ingestion Demo**

**Demo flow (UI only until backend endpoints exist):**
1. Show a form to paste a "new incident" (raw error text)
2. On submit, show "Ingesting…" then success toast (mock or real endpoint when team adds one)
3. Link back to Chat: "Now query the same error — it should appear"

**Note:** If Person 2 adds `POST /ingest` later, wire it then. For hackathon demo, a simulated delay + refetch `/query` is acceptable if coordinated with team.

**Done when:**
- Two-page app: Chat + Ingestion Demo
- Demo tells the story: new bug in → memory updated → query finds it
- All work stays inside `frontend/`

---

## Person 1 — checklist

- [ ] Phase 1: Components + HomePage
- [ ] Phase 2: LanguageToggle + polished response
- [ ] Phase 3: IngestionDemoPage + navigation
- [ ] Never edit `backend/` or `ai/`
- [ ] Flag API contract changes in team chat before implementing

---

# Person 2 — Backend (3 phases)

**Your folder:** `backend/` only  
**Your goal:** Neo4j graph, similarity search, real `/query` pipeline — same API shape.

---

## Phase 1 — Neo4j connection & seed data

**Create:**
- `app/graph/seed.py` — reads `seed_data/incidents.json`, writes nodes/relationships to AuraDB
- Expand `seed_data/incidents.json` to **15–20 realistic incidents** (keep exact field names)
- Finish `app/graph/connection.py` — real `GraphDatabase.driver()` using `.env`

**Graph model:**
- Nodes: `Incident`, `ErrorSignature`, `RootCause`, `File`, `FixPattern`, `Person`, `PR`
- Relationships: `HAS_SIGNATURE`, `CAUSED_BY`, `LOCATED_IN`, `RESOLVED_BY`, `IMPLEMENTED_IN`, `AUTHORED_BY`, `REVIEWED`, `SIMILAR_TO {score}`

**Done when:**
- `python -m app.graph.seed` (or similar) populates AuraDB
- You can query incidents in Neo4j Browser

---

## Phase 2 — Similarity search & graph traversal

**Create:**
- `app/graph/queries.py` — Cypher: given error text, find similar `ErrorSignature` nodes, traverse to `FixPattern`, `Person`, `PR`
- `app/graph/similarity.py` — confidence scoring:
  - Stack trace similarity (token overlap or call Person 3's embeddings via import/copy contract)
  - File path overlap
  - Root cause category match
- Combine into weighted `confidence` float (0.0–1.0)

**Done when:**
- Function `search_similar(error: str) -> list[dict]` returns ranked incidents
- Confidence score is explainable (even if not exposed in API yet)

---

## Phase 3 — Real `/query` endpoint

**Modify:**
- `app/main.py` — replace stub with pipeline:
  1. Accept `QueryRequest`
  2. Run similarity + graph traversal
  3. Optionally call Person 3's `generate_answer()` (import path TBD — coordinate; may duplicate thin wrapper)
  4. Return `QueryResponse` — **same fields, no renames**

**Done when:**
- `curl -X POST localhost:8000/query -d '{"error":"..."}'` returns real graph-backed results
- `language` field accepted (pass through to AI when integrated)
- Frontend works without changes if contract unchanged
- Never edit `frontend/` or `ai/` directly

---

## Person 2 — checklist

- [ ] Phase 1: AuraDB + 15–20 incidents seeded
- [ ] Phase 2: Cypher queries + confidence scoring
- [ ] Phase 3: Real `/query` replacing stub
- [ ] Never edit `frontend/` or `ai/`
- [ ] Coordinate with Person 3 on how backend invokes answer generation

---

# Person 3 — AI (2 phases)

**Your folder:** `ai/` only  
**Your goal:** Sarvam-powered extraction, answers, multilingual, embeddings.

---

## Phase 1 — Extraction & embeddings

**Modify:**
- `extraction.py` — replace `# TODO` with real Sarvam API call
  - Prompt must return JSON matching incident shape (see `backend/seed_data/incidents.json`)
  - Handle malformed input gracefully
- `embeddings.py` — real similarity (Sarvam embeddings or sentence-transformers)
  - `compute_similarity(sig_a, sig_b) -> float` used by Person 2 for ranking

**Test:**
```bash
cd ai
python extraction.py
```

**Done when:**
- Paste raw stack trace → structured dict out
- Similar errors score higher than unrelated ones in a quick manual test

---

## Phase 2 — Answers & multilingual

**Modify:**
- `answer_generation.py` — `generate_answer(graph_results, language)`:
  - Input: similar incidents, confidence, ask_person from graph traversal
  - Output: friendly paragraph for a junior dev (use Sarvam for tone)
- `multilingual.py` — `translate_answer(answer, target_lang)`:
  - Support `hi`, `ta`, `te`
  - Keep code snippets, file paths, and identifiers in English

**Done when:**
- `generate_answer()` reads mock graph_results and returns natural text
- `translate_answer()` returns Hindi/Tamil/Telugu stubs replaced with Sarvam output
- Person 2 can import/call these without you touching `backend/` (they wire it)

**Optional coordination:**
- Help team wire `ingestion/ingest_job.py` after Phase 1 — only with team sync

---

## Person 3 — checklist

- [ ] Phase 1: Sarvam extraction + embeddings
- [ ] Phase 2: Answer generation + multilingual
- [ ] Never edit `frontend/` or `backend/`
- [ ] Document function signatures if Person 2 needs to import from `ai/`

---

## Quick reference — who builds what

| Feature | Owner | Phase |
|---------|-------|-------|
| Chat UI components | Person 1 | 1 |
| Language toggle UI | Person 1 | 2 |
| Ingestion demo page | Person 1 | 3 |
| Neo4j + seed script | Person 2 | 1 |
| Graph search + confidence | Person 2 | 2 |
| Real `/query` endpoint | Person 2 | 3 |
| Sarvam extraction | Person 3 | 1 |
| Embeddings similarity | Person 3 | 1 |
| Conversational answers | Person 3 | 2 |
| Hindi/Tamil/Telugu | Person 3 | 2 |
| Render ingest pipeline | Team | after core ready |

---

*Paste your section into Cursor before starting work on your branch.*
