# Understudy

**AI pair-debugger for junior developers with institutional memory** — when a new bug comes in, Understudy surfaces "your team hit something like this before, here's the fix, here's who to ask" instead of a generic explanation.

**Sponsor tracks:** Neo4j AuraDB (graph store) · Sarvam AI (extraction + answers + multilingual) · Render Workflows (ingestion pipeline)

---

## Folder ownership (branch safety)

| Folder | Owner | Rule |
|--------|-------|------|
| `frontend/` | Person 1 | Do not modify `backend/` or `ai/` |
| `backend/` | Person 2 | Do not modify `frontend/` or `ai/` |
| `ai/` | Person 3 | Do not modify `frontend/` or `backend/` |
| `ingestion/` | Shared | Sync with team before editing |
| Root config (`.env.example`, API contract) | Shared | Sync with team before editing |

Each person works on their own git branch. See [`docs/ROLE_GUIDE.md`](docs/ROLE_GUIDE.md) for phased role instructions to paste into your IDE.

---

## How to run each part locally

### Person 1 — Frontend (`frontend/`)

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:5173`. Proxies API calls to the backend on port 8000.

Copy `.env.example` to `.env` at the repo root (or set `VITE_API_URL` in `frontend/.env`).

### Person 2 — Backend (`backend/`)

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs at `http://localhost:8000/docs`. Test the stub:

```bash
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"error\":\"TypeError: test\"}"
```

### Person 3 — AI (`ai/`)

```bash
cd ai
# From repo root, with backend venv or a shared venv:
python extraction.py
```

Modules are plain Python files. Set `SARVAM_API_KEY` in `.env` when implementing the real Sarvam call.

### Ingestion (`ingestion/`) — team sync required

```bash
cd ingestion
python ingest_job.py
```

Stub only — coordinate with Person 2 and Person 3 before wiring to Neo4j and Sarvam.

---

## Project structure

```
understudy/
├── README.md
├── .env.example
├── .gitignore
├── frontend/          # Person 1
├── backend/           # Person 2
├── ai/                # Person 3
├── ingestion/         # Shared
└── docs/
    ├── PROGRESS.md
    └── ROLE_GUIDE.md
```

---

## Interface contract (do not change without team sync)

**`POST /query`** — request: `{ "error": string, "language": "en"|"hi"|"ta"|"te" }`  
Response: `{ "answer", "confidence", "similar_incidents", "ask_person" }`

Full details in [`docs/PROGRESS.md`](docs/PROGRESS.md).
