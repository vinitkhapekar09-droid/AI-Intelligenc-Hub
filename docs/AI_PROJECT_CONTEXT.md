# AI Project Context

Last updated: 2026-04-24
Repository root: `/workspaces/ai_explore`

## How To Use This File

Use this as the project handoff file for any future AI or collaborator.

Rules:

1. Read this file before making changes.
2. Trust source code over `README.md` if they conflict.
3. Update this file after meaningful architectural or product changes.
4. Keep the `Current Reality`, `Deployment`, `Known Gaps`, and `Change Log` sections current.

Suggested prompt:

```text
Read docs/AI_PROJECT_CONTEXT.md first and use it as the source-of-truth handoff file. If the code and README disagree, trust the code. After you finish meaningful changes, update docs/AI_PROJECT_CONTEXT.md.
```

## Current Reality

This repo began as a Daily AI Digest newsletter system and is now a broader AI research product called `AI Intelligence Hub`.

Current product surfaces:

1. Public landing page
   - marketing page for non-logged-in visitors
   - shows a preview of the latest persisted issue
   - supports email subscription

2. Authenticated home/feed
   - signed-in users land on `/`, which now resolves to the persisted feed experience
   - issue archives are read from SQL, not rebuilt live on every page load

3. Research workspace
   - authenticated chat over AI news/research
   - retrieval can be filtered by `issue_date` and by `doc_type`
   - chat history is persisted by thread in the database

4. Digest pipeline
   - fetches AI news + research
   - summarizes with Gemini
   - stores a `DailyIssue` and `ContentItem` rows in SQL
   - chunks, embeds, and stores the same documents in a SQL-backed RAG chunk store
   - emails active subscribers

## What Changed Recently

Recent repo work completed:

- cleaned the project surface and moved project notes into `docs/`
- removed generated junk from the repo and tightened `.gitignore`
- changed homepage behavior so signed-in users see the feed at `/`
- limited guest navigation to `Home` and `Chat`
- hardened backend config for production
- replaced wildcard CORS with env-driven allowed origins
- protected `POST /trigger-digest` with `X-Trigger-Token`
- made frontend production API calls go through `/api`
- added Alembic and an initial schema migration
- aligned Alembic with the same dev SQLite fallback used by app startup
- isolated API tests from local dev DB state by giving them a fresh SQLite database by default
- added a low-cost DigitalOcean single-droplet deployment path
- expanded CI to include frontend build and Docker image build checks

## Tech Stack

### Frontend

- React 18
- React Router
- Axios
- Vite
- Tailwind-like utility classes via `frontend/index.html`
- additional custom CSS in `frontend/src/styles.css`

### Backend

- FastAPI
- SQLAlchemy
- Pydantic / pydantic-settings
- Alembic
- JWT auth with `python-jose`
- Argon2 password hashing via `passlib`

### Async / Data / AI

- Celery
- Redis
- PostgreSQL
- SQLite fallback in non-production if primary DB is down
- Gemini for summarization
- Groq LLaMA for chat
- Gemini embeddings API for embeddings
- SQL-backed chunk storage for retrieval
- optional MLflow tracking for summarizer runs

### Infra

- Docker / Docker Compose
- GitHub Actions
- Nginx for local/frontend container proxying
- Caddy for cheap production HTTPS on a single Droplet

## Real Directory Map

```text
backend/
  alembic/           # Alembic env + versions
  app/
    agents/          # Chat agent
    api/             # FastAPI routes
    core/            # Config, DB, auth, Celery
    models/          # User, Subscriber, Conversation, DailyIssue, ContentItem
    pipeline/        # Raw item -> unified document normalization
    rag/             # Chunking, embeddings, retrieval, vector store
    services/        # Fetcher, summarizer, email sender, digest store, conversation service
    tasks/           # Celery digest task
  alembic.ini
  requirements.txt

frontend/
  src/
    components/
    context/
    pages/
    api.js
    App.jsx
  index.html
  package.json

docs/
  AI_PROJECT_CONTEXT.md
  DEPLOY_DIGITALOCEAN.md
  DESIGN.md
  ...

infra/
  caddy/
    Caddyfile
  docker/
    Dockerfile
    Dockerfile.frontend
    nginx.conf

docker-compose.yml         # local/dev stack
docker-compose.prod.yml    # low-cost single-droplet production stack
```

## Source Of Truth Files

If someone needs to understand the current app fast, start here:

- `backend/app/api/routes.py`
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/core/database.py`
- `backend/app/core/auth.py`
- `backend/app/tasks/digest_tasks.py`
- `backend/app/agents/chat_agent.py`
- `backend/app/services/digest_store.py`
- `backend/app/services/conversation_service.py`
- `backend/app/rag/vector_store.py`
- `backend/alembic/env.py`
- `backend/alembic/versions/20260424_0001_initial_schema.py`
- `frontend/src/App.jsx`
- `frontend/src/api.js`
- `frontend/src/pages/Auth.jsx`
- `frontend/src/pages/Chat.jsx`
- `frontend/src/pages/Digest.jsx`
- `frontend/src/pages/Landing.jsx`
- `frontend/src/context/AuthContext.jsx`
- `docker-compose.prod.yml`
- `docs/DEPLOY_DIGITALOCEAN.md`

## Backend Architecture

### App startup

`backend/app/main.py`:

- creates the FastAPI app
- optionally auto-creates schema only when `AUTO_CREATE_SCHEMA=true`
- uses env-driven CORS origins
- exposes Prometheus metrics

### Configuration

`backend/app/core/config.py` is the single settings source.

Important env vars:

- `DATABASE_URL`
- `REDIS_URL`
- `GEMINI_API_KEY`
- `RESEND_API_KEY`
- `FROM_EMAIL`
- `NEWS_API_KEY`
- `MLFLOW_TRACKING_URL`
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_HOURS`
- `ENVIRONMENT`
- `CORS_ORIGINS`
- `AUTO_CREATE_SCHEMA`
- `TRIGGER_DIGEST_TOKEN`
- `GROQ_API_KEY`
- `EMBEDDING_MODEL`
- `EMBEDDING_DIMENSIONS`
- `APP_BASE_URL`

Production validation now happens in config:

- production cannot use `SECRET_KEY=CHANGE_ME`
- production requires at least one `CORS_ORIGINS` entry
- production requires `TRIGGER_DIGEST_TOKEN`

### Database behavior

`backend/app/core/database.py`:

- uses SQLAlchemy engine/session
- exposes `resolve_database_url()` as the shared DB selection path
- supports SQLite directly if `DATABASE_URL` is SQLite
- tries the primary DB first for non-SQLite URLs
- falls back to a local SQLite DB only in non-production
- fallback path is `backend/.local/daily_digest.db`

### Migrations

Alembic is now the schema migration path.

Key files:

- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/20260424_0001_initial_schema.py`

Current behavior:

- `backend/alembic/env.py` now uses the same resolved database URL as app startup
- in local/dev, `alembic upgrade head` can fall back to `backend/.local/daily_digest.db` if Postgres is unavailable

Use:

```bash
cd backend
alembic upgrade head
```

Create a migration after model changes:

```bash
cd backend
alembic revision --autogenerate -m "describe change"
```

### Auth

`backend/app/core/auth.py`:

- hashes passwords with Argon2
- creates JWTs with `sub=email`
- uses bearer token auth
- resolves current user from token and DB lookup

## Data Models

### `User`

- `id`
- `name`
- `email`
- `hashed_password`
- `is_active`
- `created_at`

### `Subscriber`

- `id`
- `email`
- `is_active`
- `subscribed_at`

### `Conversation`

- `id`
- `user_id`
- `role`
- `message`
- `doc_type`
- `sources_used`
- `created_at`
- `thread_id`
- `is_pinned`

`thread_id` is actively used by the chat UI/API to separate saved conversations. `is_pinned` exists in the schema but is still unused by the UI.

### `DailyIssue`

- `id`
- `issue_date`
- `title`
- `summary`
- `status`
- `created_at`
- `published_at`

### `ContentItem`

- `id`
- `issue_id`
- `issue_date`
- `rank`
- `doc_id`
- `title`
- `summary`
- `why_it_matters`
- `source`
- `doc_type`
- `url`
- `published_at`
- `created_at`

## API Surface

Current backend endpoints in `backend/app/api/routes.py`:

### Public

- `GET /health`
- `POST /register`
- `POST /login`
- `POST /subscribe`
- `DELETE /unsubscribe?email=...`
- `GET /daily-digest`
- `GET /issues`
- `GET /issues/{issue_date}`
- `GET /feed`
- `GET /metrics`

### Protected by trigger token

- `POST /trigger-digest`

This endpoint now requires the `X-Trigger-Token` header and should not be treated as a fully public route anymore.

### Authenticated

- `POST /chat`
- `GET /chat/threads`
- `GET /chat/history`
- `DELETE /chat/history`
- `DELETE /chat/threads/{thread_id}`
- `GET /chat/stats`

### Important endpoint notes

- auth routes are `/register` and `/login`, not `/auth/register` or `/auth/login`
- `/chat` accepts optional `doc_type`, `issue_date`, and `thread_id`
- `/chat` always resolves to a concrete `thread_id`
- `/chat/history` can load a specific thread with `thread_id`
- `/feed` can filter by `issue_date` and `doc_type`
- `/trigger-digest` is now protected by env-configured token auth

## Digest Pipeline

Main entry point: `backend/app/tasks/digest_tasks.py`

Pipeline steps:

1. fetch raw items from arXiv + NewsAPI
2. normalize them into `UnifiedDocument`
3. summarize up to 5 items with Gemini
4. store/update the SQL-backed daily issue and content items
5. send digest emails to active subscribers
6. chunk, embed, and store the same documents in SQL with `issue_date` metadata

Key modules:

- `backend/app/services/fetcher.py`
- `backend/app/pipeline/normalizer.py`
- `backend/app/services/summarizer.py`
- `backend/app/services/email_sender.py`
- `backend/app/services/digest_store.py`
- `backend/app/rag/chunker.py`
- `backend/app/rag/embedder.py`
- `backend/app/rag/vector_store.py`

MLflow is now optional in practice:

- if `MLFLOW_TRACKING_URL` is blank, summarization proceeds without MLflow logging
- this is intentional for low-cost production deployment

## RAG + Chat Architecture

### Vector storage

`backend/app/rag/vector_store.py`:

- stores normalized embeddings in the `rag_chunks` SQL table
- supports upsert-by-`chunk_id`
- filters by `doc_type` and `issue_date`
- ranks chunks in Python using cosine-equivalent dot similarity on normalized vectors

### Embeddings

`backend/app/rag/embedder.py`:

- uses Gemini embedding API
- current model default: `gemini-embedding-001`
- default output dimensionality: `768`
- normalizes embeddings before storage so retrieval can use a simple dot product

### Retrieval

`backend/app/rag/retriever.py`:

- embeds the query through the same API-based embedding path
- searches the SQL-backed chunk store
- filters low-relevance matches below `0.3`
- supports `issue_date` and `doc_type`
- formats prompt context and sources

### Chat agent

`backend/app/agents/chat_agent.py`:

- uses Groq client
- model: `llama-3.1-8b-instant`
- sanitizes input
- handles greetings and identity/meta questions
- rewrites vague prompts into retrieval-friendly queries
- enriches follow-ups from saved thread history
- generates grounded answers from retrieved context

### Conversation memory

`backend/app/services/conversation_service.py`:

- saves user and assistant messages
- returns thread history in chronological order
- lists thread summaries for the sidebar
- clears one thread or all history
- computes simple conversation stats

## Frontend Architecture

### Routing

`frontend/src/App.jsx` defines:

- `/` -> auth-aware home route
- `/auth` -> login/register
- `/chat` -> protected chat page
- `/digest` -> protected digest page
- static policy/help pages

Current home behavior:

- guests see the landing page at `/`
- signed-in users see the feed experience at `/`

### Auth state

`frontend/src/context/AuthContext.jsx`:

- stores token, username, and auth state in `localStorage`
- `logout()` clears local storage

`frontend/src/api.js`:

- injects `Authorization: Bearer <token>` if token exists
- redirects to `/auth` on `401`
- uses `http://localhost:8000` in dev and `/api` in production by default

### Pages

`Landing.jsx`

- public landing page only
- loads `/daily-digest`
- shows latest persisted issue summary plus top preview items
- supports email subscription

`Auth.jsx`

- login/register tabs
- calls `/login` and `/register`
- redirects successful auth to `/`

`Digest.jsx`

- protected feed/archive page
- loads `/daily-digest` or `/issues/{issue_date}`
- loads `/issues` for archive chips

`Chat.jsx`

- protected chat workspace
- loads `/issues` to build date scopes
- loads `/chat/threads` for the sidebar
- loads `/chat/history`
- supports true saved threads
- supports `doc_type` filter: `All`, `Research`, `News`
- supports issue scope: all issues or one issue date

### Navigation behavior

`frontend/src/components/Navbar.jsx`:

- guests: `Home`, `Chat`
- authenticated users: `Home`, `Research`

Because `/` is now auth-aware, the old separate top-level feed nav item was removed.

## Runtime And Deployment

### Local/dev stack

`docker-compose.yml` includes:

- `db`
- `redis`
- `mlflow`
- `api`
- `worker`
- `beat`
- `frontend`

Local frontend talks to backend through `/api` inside the Nginx container.

### Cheap production stack

`docker-compose.prod.yml` is the current recommended deployment path for a cost-constrained launch.

Services:

- `db`
- `redis`
- `api`
- `worker`
- `beat`
- `frontend`
- `caddy`

Key production choices:

- single DigitalOcean Droplet
- Caddy handles HTTPS
- MLflow disabled by default
- API container runs `alembic upgrade head` before starting Uvicorn
- frontend uses `/api` proxying instead of a hardcoded backend hostname

Main deployment doc:

- `docs/DEPLOY_DIGITALOCEAN.md`

Main production env template:

- `.env.production.example`

## CI/CD

### CI

`.github/workflows/ci.yml` now:

- runs on push/PR to `dev` or `main`
- provisions Postgres and Redis
- installs Python deps
- lints `backend/app` with flake8
- runs backend pytest
- installs frontend deps
- builds the frontend
- builds backend and frontend Docker images without pushing

### Deployment workflow

`.github/workflows/deploy-droplet.yml`:

- deploys to a pre-provisioned DigitalOcean Droplet over SSH
- assumes repo lives at `/opt/ai_explore`
- assumes `.env.production` already exists on the server
- runs `docker compose -f docker-compose.prod.yml up -d --build --remove-orphans`

## How To Run Key Commands Yourself

### Restore frontend dependencies

```bash
cd /workspaces/ai_explore/frontend
npm install
```

### Recommended local demo run

Terminal 1:

```bash
cd /workspaces/ai_explore
./.venv/bin/python scripts/populate_project.py --mode demo --days 3
bash scripts/run_local_backend.sh
```

Terminal 2:

```bash
cd /workspaces/ai_explore
bash scripts/run_local_frontend.sh
```

This is now the preferred local path because:

- backend uses the known SQLite demo DB
- frontend proxies `/api` through Vite
- no manual CORS tweaking or port juggling is needed

### Run backend tests

```bash
cd /workspaces/ai_explore
./.venv/bin/pytest tests/test_api.py -v
```

Test behavior:

- `tests/test_api.py` now defaults to a fresh temporary SQLite file each run
- local dev subscriber data should no longer leak into API test outcomes
- set `TEST_DATABASE_URL` if you want to force a specific test database

If the environment is flaky, force explicit test env vars:

```bash
cd /workspaces/ai_explore
env \
  TEST_DATABASE_URL=sqlite:///test_api_fresh.db \
  GEMINI_API_KEY=test \
  RESEND_API_KEY=test \
  NEWS_API_KEY=test \
  MLFLOW_TRACKING_URL=http://localhost:5000 \
  SECRET_KEY=test-secret-key \
  ENVIRONMENT=testing \
  TRIGGER_DIGEST_TOKEN=test-trigger-token \
  ./.venv/bin/pytest tests/test_api.py -vv
```

### Run Alembic migrations locally

```bash
cd /workspaces/ai_explore/backend
alembic upgrade head
```

### Create a new Alembic migration

```bash
cd /workspaces/ai_explore/backend
alembic revision --autogenerate -m "describe change"
```

### Build the frontend

```bash
cd /workspaces/ai_explore/frontend
VITE_API_BASE=/api npm run build
```

### Start the cheap production stack locally

```bash
cd /workspaces/ai_explore
cp .env.production.example .env.production
docker compose -f docker-compose.prod.yml up -d --build
```

### Codespaces-friendly Docker run

```bash
cd /workspaces/ai_explore
docker compose -f docker-compose.yml -f docker-compose.codespaces.yml up --build db redis api frontend
```

Enable worker, beat, and mlflow only when needed:

```bash
docker compose -f docker-compose.yml -f docker-compose.codespaces.yml --profile full up --build
```

### Populate demo data quickly

```bash
cd /workspaces/ai_explore
./.venv/bin/python scripts/populate_project.py --mode demo --days 3
```

### Populate live data with real APIs

```bash
cd /workspaces/ai_explore
./.venv/bin/python scripts/populate_project.py --mode live --max-items 8
```

### Run the smoke test

```bash
cd /workspaces/ai_explore
./.venv/bin/python scripts/smoke_test.py --base-url http://localhost:8000 --expect-data
```

### Check production-style logs

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f worker
```

## Known Gaps

Important current caveats:

1. `README.md` is improved but still retains some older digest-era framing.
2. Product naming is still mixed between `Daily AI Digest` and `AI Intelligence Hub`.
3. Full local verification is not fully settled yet because:
   - frontend dependencies were cleaned and need reinstall before frontend build can be rerun locally
   - `pytest tests/test_api.py` was observed hanging during collection in this environment and may need debugging
4. Alembic exists now, but only the initial migration has been added so far.
5. Production deploy workflow assumes the Droplet is already provisioned manually once.
6. `is_pinned` exists in the conversation schema but has no current product flow.
7. Daily task run tracking exists now, but alerting/notifications for failures still do not.

## Change Log

### 2026-04-24

- reorganized docs under `docs/`
- cleaned generated files and tightened `.gitignore`
- changed signed-in homepage behavior to feed-at-root
- simplified guest navigation
- hardened backend config for production
- protected `/trigger-digest` with trigger-token auth
- changed frontend production API base to `/api`
- improved local/frontend proxy behavior
- added Alembic and initial schema migration
- aligned Alembic migrations with the dev SQLite fallback path
- isolated API tests with a fresh temporary SQLite DB by default
- made MLflow optional in low-cost production
- added `docker-compose.prod.yml`
- added Caddy-based single-droplet deployment path
- added DigitalOcean deployment documentation
- expanded CI and added droplet deploy workflow
- added `scripts/populate_project.py` for demo or live data seeding
- added `scripts/run_local_backend.sh` and `scripts/run_local_frontend.sh`
- added `docker-compose.codespaces.yml` for a lighter Codespaces run path
- added `task_runs` tracking, `/health/details`, and `scripts/smoke_test.py`
