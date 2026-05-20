# AI Project Context

Last updated: 2026-04-28 10:45 UTC
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
   - runs automatically at 8:00 AM IST daily via Celery Beat

## What Changed Recently

Recent repo work completed (2026-04-27 deployment session):

- fixed chat route: `async def chat` and `await ask()` — was causing `TypeError: coroutine object is not subscriptable`
- fixed Celery Beat schedule UTC math: `crontab(hour=2, minute=30)` = 8:00 AM IST
- added explicit `appnet` Docker network to `docker-compose.prod.yml` so all services can resolve each other by name
- fixed Caddyfile to route `/api/*` to backend and everything else to frontend
- removed old `deploy-droplet.yml` workflow that was conflicting with new deploy pipeline
- added `deploy.yml` — SSH-based auto-deploy workflow triggered on push to `main`
- deployed to DigitalOcean droplet at `165.22.222.157`
- enabled UFW firewall (ports 22, 80, 443 only) — TODO: still needs to be done
- app is live and serving HTTP on `http://165.22.222.157`

Previous repo work completed (2026-04-24):

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
- GitHub Actions (CI + auto-deploy)
- Nginx for local/frontend container proxying
- Caddy for production HTTP/HTTPS on a single Droplet
- DigitalOcean droplet: `165.22.222.157` (Ubuntu 24.04, 1vCPU 2GB RAM)

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
    Caddyfile          # routes /api/* to backend, everything else to frontend
  docker/
    Dockerfile
    Dockerfile.frontend
    nginx.conf

.github/
  workflows/
    ci.yml             # test + lint on push to dev or main
    cd.yml             # build and push docker image
    deploy.yml         # SSH deploy to DigitalOcean on push to main

docker-compose.yml         # local/dev stack
docker-compose.prod.yml    # low-cost single-droplet production stack (with appnet network)
```

## Source Of Truth Files

If someone needs to understand the current app fast, start here:

- `backend/app/api/routes.py`
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/core/database.py`
- `backend/app/core/auth.py`
- `backend/app/core/celery_app.py`
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
- `infra/caddy/Caddyfile`
- `.github/workflows/deploy.yml`
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
- `APP_DOMAIN`
- `ACME_EMAIL`

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
- in production, `alembic upgrade head` runs automatically before Uvicorn starts (see `docker-compose.prod.yml` api command)

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

### Celery Beat Schedule

`backend/app/core/celery_app.py`:

- broker and backend: Redis
- timezone: `Asia/Kolkata` with `enable_utc=True`
- beat schedule: `crontab(hour=2, minute=30)` = 8:00 AM IST = 2:30 AM UTC
- task: `app.tasks.digest_tasks.run_daily_digest`

**Important:** Because `enable_utc=True`, the crontab must be specified in UTC. 2:30 AM UTC = 8:00 AM IST.

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

Requires `X-Trigger-Token` header matching `TRIGGER_DIGEST_TOKEN` env var. Use to manually trigger the digest pipeline:

```bash
curl -X POST http://165.22.222.157/api/trigger-digest \
  -H "X-Trigger-Token: your_token_here"
```

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
- `/trigger-digest` is protected by env-configured token auth
- the `chat` route is `async def` and calls `await ask()` — both must stay async

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
- `ask()` is `async def` — must always be called with `await`
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

### Production stack

`docker-compose.prod.yml` is the current recommended deployment path.

Services:

- `db`
- `redis`
- `api`
- `worker`
- `beat`
- `frontend`
- `caddy`

All services are on the explicit `appnet` bridge network so container DNS resolution works correctly (e.g. Caddy can reach `api:8000`).

Key production choices:

- single DigitalOcean Droplet at `165.22.222.157`
- Caddy handles routing (HTTP for now, HTTPS ready when domain is added)
- MLflow disabled by default
- API container runs `alembic upgrade head` before starting Uvicorn
- frontend uses `/api` proxying instead of a hardcoded backend hostname

### Caddyfile

Current Caddyfile (`infra/caddy/Caddyfile`) routes HTTP on port 80:

```
:80 {
    encode gzip zstd

    handle /api/* {
        uri strip_prefix /api
        reverse_proxy api:8000
    }

    handle {
        reverse_proxy frontend:80
    }
}
```

When a domain is added, update to:

```
yourdomain.com {
    encode gzip zstd
    tls your@email.com

    handle /api/* {
        uri strip_prefix /api
        reverse_proxy api:8000
    }

    handle {
        reverse_proxy frontend:80
    }
}
```

And update `.env.production`:
```
APP_DOMAIN=yourdomain.com
ACME_EMAIL=your@email.com
APP_BASE_URL=https://yourdomain.com
CORS_ORIGINS=https://yourdomain.com
```

Main deployment doc:

- `docs/DEPLOY_DIGITALOCEAN.md`

Main production env template:

- `.env.production.example`

## CI/CD

### CI

`.github/workflows/ci.yml`:

- runs on push/PR to `dev` or `main`
- provisions Postgres and Redis
- installs Python deps
- lints `backend/app` with flake8
- runs backend pytest
- installs frontend deps
- builds the frontend

### CD

`.github/workflows/cd.yml`:

- builds backend and frontend Docker images

### Deploy

`.github/workflows/deploy.yml`:

- triggers only on push to `main`
- SSHs into the DigitalOcean droplet using `DO_SSH_PRIVATE_KEY` secret
- runs `git pull origin main`
- runs `docker compose -f docker-compose.prod.yml up -d --build --remove-orphans`
- runs `docker image prune -f`

Required GitHub secrets:

| Secret | Value |
|--------|-------|
| `DO_HOST` | `165.22.222.157` |
| `DO_SSH_USER` | `root` |
| `DO_SSH_PRIVATE_KEY` | Contents of `~/.ssh/deploy_key` on the droplet |

The deploy key is at `~/.ssh/deploy_key` on the droplet. Public key is in `~/.ssh/authorized_keys`.

### Branch strategy

- work on `dev` branch
- merge to `main` when ready to deploy
- every push to `main` auto-deploys to the droplet

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

### Run backend tests

```bash
cd /workspaces/ai_explore
./.venv/bin/pytest tests/test_api.py -v
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

### Manually trigger digest on production

```bash
curl -X POST http://165.22.222.157/api/trigger-digest \
  -H "X-Trigger-Token: your_trigger_token"
```

### Watch production logs

```bash
ssh root@165.22.222.157
cd /opt/ai_explore
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f worker
docker compose -f docker-compose.prod.yml logs -f beat
```

### Check production container status

```bash
ssh root@165.22.222.157
cd /opt/ai_explore
docker compose -f docker-compose.prod.yml ps
```

### Deploy manually (without GitHub Actions)

```bash
ssh root@165.22.222.157
cd /opt/ai_explore
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build --remove-orphans
docker image prune -f
```

## Known Gaps

Important current caveats:

1. `README.md` still retains some older digest-era framing.
2. Product naming is still mixed between `Daily AI Digest` and `AI Intelligence Hub`.
3. No HTTPS yet — running on raw HTTP. Needs a domain + Caddyfile update to enable TLS.
4. No UFW firewall enabled yet on the droplet — all ports are open.
5. No rate limiting on `/login`, `/register`, `/chat` — vulnerable to brute force.
6. Root SSH login is enabled — should create a non-root deploy user.
7. No request size limits on `/chat` — large payloads could spike API costs.
8. JWT tokens are not revocable — stolen tokens stay valid until expiry.
9. `is_pinned` exists in the conversation schema but has no current product flow.
10. Daily task run tracking exists, but alerting/notifications for failures still do not.
11. Alembic exists with only the initial migration so far.
12. `pytest tests/test_api.py` was observed hanging during collection in Codespaces — may need debugging.

## Security Checklist (Priority Order)

- [ ] Enable UFW firewall: `ufw allow 22 && ufw allow 80 && ufw allow 443 && ufw enable`
- [ ] Get domain and enable HTTPS via Caddy
- [ ] Add rate limiting with `slowapi` on `/login`, `/register`, `/chat`
- [ ] Create non-root SSH user and disable root login
- [ ] Add request size limits in FastAPI
- [ ] Add JWT token revocation via Redis blocklist

## Change Log

### 2026-04-28

- added retrying `docker pull` prefetches in `.github/workflows/deploy.yml` so transient Docker Hub timeouts are less likely to break SSH deploys
- fix: restore correct celery worker command and remove beat schedule (1bdfc2b)
- fix: add retry logic and network resilience to frontend Docker build (306dc5d)
- fix: correct celery worker app reference to celery_app:celery_app (3c4884c)
- fix: remove beat reference from deploy workflow (7927f62)
- fix: replace Celery Beat with Linux cron for reliable daily schedule (2092d71)

### 2026-04-27

- fixed critical bug: chat route was `def` calling `async ask()` without `await` — caused `TypeError: coroutine object is not subscriptable`
- fixed Celery Beat schedule: corrected UTC math so 8AM IST fires correctly at `crontab(hour=2, minute=30)`
- added explicit `appnet` bridge network to `docker-compose.prod.yml` — fixes Caddy DNS resolution to API container
- fixed Caddyfile: added `/api/*` routing to backend, all other traffic to frontend
- removed conflicting `deploy-droplet.yml` workflow
- added `deploy.yml` — SSH-based GitHub Actions auto-deploy on push to `main`
- completed fresh DigitalOcean deployment at `165.22.222.157`
- app is live and fully operational: frontend, API, chat, RAG, Celery Beat all running

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