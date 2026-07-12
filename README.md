# Understudy

**AI pair-debugger for junior developers with institutional memory** — when a new bug comes in, Understudy surfaces "your team hit something like this before, here's the fix, here's who to ask" instead of a generic explanation.

**Sponsor tracks:** Neo4j AuraDB (graph store) · Sarvam AI (extraction + answers + multilingual) · Render Workflows (ingestion pipeline)

---

## Quick start (full stack)

1. Copy env and fill real values when ready (placeholders are ignored safely):

```bash
cp .env.example .env
```

2. Backend:

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
# Optional AI extras (embeddings model):
pip install -r ../ai/requirements.txt

uvicorn app.main:app --reload --port 8000
```

3. Frontend (new terminal):

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

4. Optional — seed Neo4j after setting Aura credentials:

```bash
cd backend
python -m app.graph.seed
```

Without Neo4j/Sarvam keys the app still runs using seed JSON + template answers.

---

## Folder ownership (branch safety)

| Folder | Owner | Rule |
|--------|-------|------|
| `frontend/` | Person 1 | Do not modify `backend/` or `ai/` |
| `backend/` | Person 2 | Do not modify `frontend/` or `ai/` |
| `ai/` | Person 3 | Do not modify `frontend/` or `backend/` |
| `ingestion/` | Shared | Sync with team before editing |
| Root config (`.env.example`, API contract) | Shared | Sync with team before editing |

See [`docs/ROLE_GUIDE.md`](docs/ROLE_GUIDE.md) for phased role instructions.

---

## API

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Status + incident source |
| `POST` | `/query` | Similarity search → answer |
| `POST` | `/ingest` | Extract + store a new incident |

**`POST /query`** — `{ "error": string, "language": "en"|"hi"|"ta"|"te" }`  
Response: `{ "answer", "confidence", "similar_incidents", "ask_person" }`

**`POST /ingest`** — `{ "raw": string }`  
Response: `{ "status", "id", "title", "neo4j_written", "storage", "message" }`

---

## Ingestion CLI

```bash
cd ingestion
python ingest_job.py seed
python ingest_job.py raw "TypeError: Cannot read property 'map' of undefined"
```

---

## Project structure

```
understudy/
├── README.md
├── .env.example
├── frontend/          # React chat + ingestion demo
├── backend/           # FastAPI + Neo4j + /query + /ingest
├── ai/                # Sarvam extraction / answers / multilingual / embeddings
├── ingestion/         # Render-ready ingest job
└── docs/
```

Full status: [`docs/PROGRESS.md`](docs/PROGRESS.md).
