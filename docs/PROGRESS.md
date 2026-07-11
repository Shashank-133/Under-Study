# Understudy — Progress & Living Doc

## 1. Project summary

**Understudy** is an AI pair-debugger for junior developers with institutional memory. It uses a Neo4j knowledge graph to remember past bugs, root causes, fixes, and who fixed them — so new errors surface "your team hit this before, here's the fix, here's who to ask."

**Sponsor tracks:** Neo4j AuraDB · Sarvam AI · Render Workflows

---

## 2. What's done so far

### Root
- [x] `README.md` — pitch, ownership rules, run instructions
- [x] `.env.example` — Neo4j, Sarvam, Render, Vite API URL placeholders
- [x] `.gitignore` — Python + Node + `.env`

### Frontend (Person 1)
- [x] `frontend/package.json` — React 18 + Vite
- [x] `frontend/vite.config.js` — dev proxy to backend
- [x] `frontend/index.html`, `frontend/src/main.jsx`
- [x] `frontend/src/App.jsx` — chat UI wired to `POST /query`
- [x] `frontend/src/App.css` — minimal dark theme
- [x] `frontend/src/components/`, `frontend/src/pages/` — empty, ready to build

### Backend (Person 2)
- [x] `backend/requirements.txt`
- [x] `backend/app/main.py` — FastAPI + stub `/query` + `/health`
- [x] `backend/app/api/query.py` — frozen request/response models
- [x] `backend/app/models/incident.py` — Pydantic models matching graph schema
- [x] `backend/app/graph/connection.py` — Neo4j driver stub
- [x] `backend/seed_data/incidents.json` — 4 example incidents

### AI (Person 3)
- [x] `ai/extraction.py` — `extract_incident()` stub + Sarvam TODO
- [x] `ai/answer_generation.py` — `generate_answer()` stub
- [x] `ai/multilingual.py` — `translate_answer()` stub (hi/ta/te)
- [x] `ai/embeddings.py` — `compute_similarity()` stub

### Shared
- [x] `ingestion/ingest_job.py` — Render-ready stub
- [x] `docs/PROGRESS.md` — this file
- [x] `docs/ROLE_GUIDE.md` — per-person phased IDE context

---

## 3. Current architecture

```
Junior dev pastes error
        │
        ▼
  frontend/ (React chat UI)
        │  POST /query { error, language }
        ▼
  backend/ (FastAPI)
        │  [stub today] → [Neo4j graph + AI pipeline later]
        ▼
  Response { answer, confidence, similar_incidents, ask_person }
```

**Graph data model (nodes):** `Incident`, `ErrorSignature`, `RootCause`, `File`, `FixPattern`, `Person`, `PR`

**Relationships:** `HAS_SIGNATURE`, `CAUSED_BY`, `LOCATED_IN`, `RESOLVED_BY`, `IMPLEMENTED_IN`, `AUTHORED_BY`, `REVIEWED`, `SIMILAR_TO {score}`

**AI modules (called by backend/ingestion later):** extraction → embeddings for similarity → answer_generation → multilingual

---

## 4. What each person needs to do next

### Person 1 — Frontend
- Build out full chat UI in `frontend/src/components/` and `frontend/src/pages/`
- Keep wired to `/query`; add language-toggle display behavior
- Build live ingestion demo view
- Do not modify `backend/` or `ai/`

### Person 2 — Backend
- Real Neo4j AuraDB connection in `backend/app/graph/`
- Expand seed data to 15–20 incidents; write seed script
- Similarity search + graph traversal + confidence scoring
- Replace stub `/query` logic (same request/response shape)
- Do not modify `frontend/` or `ai/`

### Person 3 — AI
- Real `extract_incident()` via Sarvam
- `answer_generation.py` — conversational answers from graph results
- `multilingual.py` — Hindi/Tamil/Telugu with code terms preserved
- `embeddings.py` — error signature similarity
- Do not modify `frontend/` or `backend/`

See **`docs/ROLE_GUIDE.md`** for detailed phased breakdown per role.

---

## 5. Phase 2 — Future Enhancements

| Idea | Owner |
|------|-------|
| WebSocket live updates for ingestion demo | Person 1 / frontend |
| Graph visualization of similar incidents | Person 1 / frontend |
| Confidence score breakdown UI (stack vs file vs category) | Person 1 / frontend |
| Slack/GitHub webhook auto-ingestion | Person 3 / ingestion |
| Cypher query caching layer | Person 2 / backend |
| Telugu voice input via Sarvam | Person 3 / ai |
| Team admin dashboard for incident review | Person 1 / frontend |

---

## 6. Known interface contracts (do not change without team sync)

### `POST /query`

**Request:**
```json
{
  "error": "string (required)",
  "language": "en | hi | ta | te (optional, default en)"
}
```

**Response:**
```json
{
  "answer": "string",
  "confidence": 0.0,
  "similar_incidents": [
    {
      "id": "string",
      "title": "string",
      "similarity_score": 0.0,
      "fix_summary": "string",
      "resolved_by": "string",
      "pr_url": "string"
    }
  ],
  "ask_person": "string | null"
}
```

### `.env` variable names
`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `SARVAM_API_KEY`, `RENDER_API_KEY`, `VITE_API_URL`

### Incident JSON field names
`id`, `title`, `description`, `created_at`, `error_signature` (`message`, `stack_trace`, `error_type`), `root_cause` (`category`, `description`), `files` (`path`, `line`), `fix_pattern` (`description`, `code_snippet`), `resolved_by` (`name`, `email`), `pr` (`number`, `url`, `title`), `similar_to` (`incident_id`, `score`)

---

*Last updated: initial skeleton setup pass.*
