# Understudy — Progress & Living Doc

## 1. Project summary

**Understudy** is an AI pair-debugger for junior developers with institutional memory. It uses a Neo4j knowledge graph to remember past bugs, root causes, fixes, and who fixed them — so new errors surface "your team hit this before, here's the fix, here's who to ask."

**Sponsor tracks:** Neo4j AuraDB · Sarvam AI · Render Workflows

---

## 2. What's done

### Root
- [x] `README.md`, `.env.example`, `.gitignore`
- [x] Docs: `PROGRESS.md`, `ROLE_GUIDE.md`

### Frontend (Person 1)
- [x] Chat UI with language toggle (`en|hi|ta|te`)
- [x] Response card: answer, confidence, ask_person, similar incidents, PR links
- [x] Ingestion demo page → `POST /ingest`, then "Try in Chat"
- [x] Vite proxy for `/query`, `/ingest`, `/health`
- [x] Components under `frontend/src/components/` (reusable building blocks)

### Backend (Person 2)
- [x] Real Neo4j AuraDB driver (`app/graph/connection.py`)
- [x] Seed script + **18** incidents (`python -m app.graph.seed`)
- [x] Similarity search + confidence scoring (`queries.py`, `similarity.py`)
- [x] Real `POST /query` (seed JSON fallback when Neo4j unset)
- [x] Real `POST /ingest` (runtime store + Neo4j when configured)
- [x] AI bridge (`app/ai_bridge.py`) → Person 3 modules when importable

### AI (Person 3)
- [x] `extraction.py` — Sarvam chat extraction + stub fallback
- [x] `embeddings.py` — sentence-transformers + token-overlap fallback
- [x] `answer_generation.py` — Sarvam conversational answers + template fallback
- [x] `multilingual.py` — hi/ta/te with code-span preservation
- [x] See `ai/PERSON3_WORK_LOG.md`

### Shared ingestion
- [x] `ingestion/ingest_job.py` — seed or raw → extract/write via backend services

---

## 3. Architecture (current)

```
Junior dev pastes error
        │
        ▼
  frontend/  POST /query { error, language }
        │
        ▼
  backend/  similarity (Neo4j | seed + runtime) → ai.generate_answer
        │
        ▼
  { answer, confidence, similar_incidents, ask_person }

Ingestion demo / Render job
        │
        ▼
  POST /ingest or ingest_job.py
        │
        ▼
  ai.extract_incident → Neo4j (optional) + runtime store
```

---

## 4. Env vars

| Var | Required for | Where to get |
|-----|--------------|--------------|
| `NEO4J_URI` / `USER` / `PASSWORD` | AuraDB graph | https://console.neo4j.io |
| `SARVAM_API_KEY` | Real extraction / answers / translate | https://dashboard.sarvam.ai/key-management |
| `RENDER_API_KEY` | Render workflows later | https://dashboard.render.com/u/settings#api-keys |
| `VITE_API_URL` | Frontend → API | Local default `http://localhost:8000` |

Placeholder values are treated as unset so local demos keep working.

---

## 5. Phase 2 — Future enhancements

| Idea | Owner |
|------|-------|
| WebSocket live updates for ingestion | Frontend |
| Graph visualization | Frontend |
| Confidence breakdown UI | Frontend |
| Slack/GitHub webhook auto-ingestion | Ingestion |
| Cypher query caching | Backend |
| Telugu voice input via Sarvam | AI |

---

## 6. Frozen API contract

Unchanged request/response field names for `POST /query` — see ROLE_GUIDE.

`POST /ingest`: `{ "raw": string }` → `{ status, id, title, neo4j_written, storage, message }`

---

*Last updated: full-stack integration pass.*
