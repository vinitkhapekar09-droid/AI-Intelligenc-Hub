# 🤖 Daily AI Digest

A production-grade AI-powered newsletter system that automatically fetches the latest AI/ML research and news, summarizes it in plain English using Google Gemini, and delivers it to subscribers via email every morning.

Built as a end-to-end MLOps/DevOps learning project covering the full engineering stack.

---

## 🚀 Live Pipeline
arXiv + NewsAPI → Gemini LLM → Email (Resend) → Subscriber
↓                ↓
PostgreSQL       MLflow Tracking
↓
Prometheus + Grafana

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Python 3.11 |
| Database | PostgreSQL (SQLAlchemy + Alembic) |
| Task Queue | Celery + Redis |
| Scheduling | Celery Beat (daily 7AM IST) |
| LLM | Google Gemini 2.0 Flash |
| Email | Resend |
| Retrieval | SQL-backed RAG chunks + Gemini embeddings |
| LLMOps | MLflow (optional prompt tracking, latency, token logs) |
| Containerization | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Monitoring | Prometheus + Grafana |

---

## 📦 Services (Docker Compose)

| Service | Description | Port |
|---|---|---|
| `api` | FastAPI backend | 8000 |
| `worker` | Celery task executor | — |
| `beat` | Celery scheduler (7AM daily) | — |
| `db` | PostgreSQL database | 5432 |
| `redis` | Message broker | 6379 |
| `mlflow` | LLM experiment tracking | 5000 |
| `flower` | Celery task monitor | 5555 |
| `prometheus` | Metrics scraper | 9090 |
| `grafana` | Metrics dashboard | 3000 |

---

## 🏗️ Project Structure

```text
ai_explore/
├── backend/               # FastAPI app, RAG pipeline, Celery tasks
├── frontend/              # Vite + React client
├── infra/                 # Docker and Prometheus config
├── tests/                 # Shared pytest suite
├── docs/                  # Product, auth, design, and project notes
├── .github/workflows/     # CI/CD pipelines
├── docker-compose.yml     # Full stack orchestration
└── README.md
```

## 📚 Project Docs

- `docs/AI_PROJECT_CONTEXT.md` - current product and project context
- `docs/DESIGN.md` - design notes and UI direction
- `docs/AUTH_SYSTEM_GUIDE.md` - auth architecture and flows
- `docs/QUICK_START_AUTH.md` - auth setup quick start
- `docs/FIXES_COMPLETE.md` - implementation fix log
- `docs/FRONTEND_FIXES_SUMMARY.md` - frontend-focused changes summary
- `docs/DEPLOY_DIGITALOCEAN.md` - low-cost single-droplet deployment guide
- `docs/project.txt` - original project outline

## 🗃️ Database Migrations

The backend now uses Alembic for schema changes.

```bash
cd backend
alembic upgrade head
```

Create a new migration after model changes:

```bash
cd backend
alembic revision --autogenerate -m "describe change"
```

## 🌱 Populate Demo Data

Seed a few realistic daily issues without external API keys:

```bash
cd /workspaces/ai_explore
./.venv/bin/python scripts/populate_project.py --mode demo --days 3
```

Use live APIs instead:

```bash
cd /workspaces/ai_explore
./.venv/bin/python scripts/populate_project.py --mode live --max-items 8
```

## ▶️ Local Demo Run

Recommended non-Docker local flow:

```bash
cd /workspaces/ai_explore
./.venv/bin/python scripts/populate_project.py --mode demo --days 3
bash scripts/run_local_backend.sh
```

In a second terminal:

```bash
cd /workspaces/ai_explore
bash scripts/run_local_frontend.sh
```

This keeps the backend on a known SQLite file and makes the Vite frontend proxy `/api` to the backend automatically.

## ✅ Smoke Test

Verify the backend quickly:

```bash
cd /workspaces/ai_explore
./.venv/bin/python scripts/smoke_test.py --base-url http://localhost:8000
```

Require real feed/RAG data too:

```bash
cd /workspaces/ai_explore
./.venv/bin/python scripts/smoke_test.py --base-url http://localhost:8000 --expect-data
```

## 🐳 Codespaces Docker Run

Use the lighter Codespaces overlay instead of the full stack:

```bash
cd /workspaces/ai_explore
docker compose -f docker-compose.yml -f docker-compose.codespaces.yml up --build db redis api frontend
```

Only enable heavier background services when you need them:

```bash
docker compose -f docker-compose.yml -f docker-compose.codespaces.yml --profile full up --build
```

---

## 🔄 How It Works

1. **Celery Beat** triggers `run_daily_digest` task every morning at 7AM IST
2. **Fetcher** pulls latest papers from arXiv (`cs.AI`, `cs.LG`, `stat.ML`) and articles from NewsAPI
3. **Summarizer** sends top 5 items to Gemini with a structured prompt, gets back plain English summaries with "why it matters" sections
4. **MLflow** logs every LLM call — model name, prompt, response, latency, token count
5. **Email sender** renders an HTML digest and delivers it to all active subscribers via Resend
6. **Prometheus** scrapes API metrics every 15 seconds, **Grafana** visualizes them

---

## 🛠️ Local Setup

### Prerequisites
- Docker + Docker Compose
- Git

### 1. Clone the repo
```bash
git clone https://github.com/Vinitkhapekar/daily-ai-digest.git
cd daily-ai-digest
```

### 2. Set up environment variables
```bash
cp .env.example .env
# Fill in your API keys in .env
```

### 3. Start all services
```bash
docker compose up --build
```

### 4. Subscribe and trigger a digest
```bash
# Subscribe
curl -X POST http://localhost:8000/subscribe \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com"}'

# Manually trigger digest
curl -X POST http://localhost:8000/trigger-digest
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/subscribe` | Subscribe with email |
| DELETE | `/unsubscribe?email=` | Unsubscribe |
| POST | `/trigger-digest` | Manually trigger digest |
| GET | `/metrics` | Prometheus metrics |

---

## 🧪 Running Tests

```bash
pip install pytest httpx
pytest tests/ -v
```

---

## 📊 Monitoring

| Tool | URL | Credentials |
|---|---|---|
| FastAPI Docs | http://localhost:8000/docs | — |
| MLflow UI | http://localhost:5000 | — |
| Flower | http://localhost:5555 | — |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3000 | admin / admin123 |

---

## 🔁 CI/CD

- **CI** (`ci.yml`) — runs on every push/PR to `dev` or `main`: installs deps, lints with flake8, runs pytest
- **CD** (`cd.yml`) — runs on merge to `main`: builds and pushes Docker image to Docker Hub

---

## 📈 MLflow Tracking

Every Gemini API call is logged as an MLflow run with:
- Model name and version
- Prompt length and content
- Number of summaries returned
- Latency in seconds
- Full prompt and response stored as artifacts

---

## 🧠 Key Engineering Decisions

**Why Celery over cron?** Celery gives retries on failure, task visibility via Flower, and distributed execution — a plain cron job gives none of that.

**Why MLflow for an LLM app?** Treating every LLM call as an experiment lets you compare prompt versions, track cost over time, and catch quality regressions — exactly what LLMOps means in practice.

**Why NullPool for PostgreSQL?** Celery workers fork processes — connection pools don't survive forks cleanly. NullPool creates a fresh connection per request, avoiding pool exhaustion errors.

---

## 👤 Author

**Vinit Khapekar**  
# deployed Sat Apr 25 07:22:50 UTC 2026
