# DigitalOcean Droplet Deployment

This project is set up to run cheaply on a single DigitalOcean Droplet using Docker Compose.

## Recommended Droplet Size

- `Basic 2 GiB / 1 vCPU` for development, demos, and very light traffic
- `Basic 4 GiB / 2 vCPU` if you expect regular background digest jobs and a few real users

## What Runs on the Droplet

- `caddy` for HTTPS and public traffic
- `frontend` for the React app
- `api` for FastAPI
- `worker` for Celery background jobs
- `beat` for the scheduled daily digest
- `db` for PostgreSQL
- `redis` for Celery broker/state

This keeps costs low by avoiding managed Postgres, managed Redis, and App Platform components.

## One-Time Server Setup

1. Create an Ubuntu 24.04 Droplet.
2. Point your domain DNS `A` record to the Droplet IP.
3. Install Docker and the Compose plugin.
4. Clone the repo into `/opt/ai_explore`.
5. Copy `.env.production.example` to `.env.production` and fill in real secrets.

Example:

```bash
sudo mkdir -p /opt
cd /opt
git clone https://github.com/your-org/ai_explore.git
cd ai_explore
cp .env.production.example .env.production
```

## Required Production Env

Set these in `.env.production`:

- `APP_DOMAIN`
- `ACME_EMAIL`
- `SECRET_KEY`
- `TRIGGER_DIGEST_TOKEN`
- `DATABASE_URL`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `REDIS_URL`
- `GEMINI_API_KEY`
- `NEWS_API_KEY`
- `RESEND_API_KEY`
- `FROM_EMAIL`

Optional:

- `GROQ_API_KEY`
- `MLFLOW_TRACKING_URL`

## Deploy

Run:

```bash
cd /opt/ai_explore
docker compose -f docker-compose.prod.yml up -d --build
```

Check status:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f api
```

## Migrations

The production API container runs:

```bash
alembic upgrade head
```

before starting Uvicorn.

You can also run migrations manually:

```bash
cd /opt/ai_explore/backend
alembic upgrade head
```

## GitHub Actions Deployment

The repo includes `.github/workflows/deploy-droplet.yml`.

Add these GitHub secrets:

- `DROPLET_HOST`
- `DROPLET_USER`
- `DROPLET_SSH_KEY`

The workflow assumes:

- the repo already exists at `/opt/ai_explore`
- `.env.production` is already present on the server
- Docker is already installed

## Notes

- HTTPS is terminated by Caddy using Let's Encrypt.
- The frontend calls the backend through `/api`, so the browser never needs to know the internal container hostname.
- MLflow is disabled by default in the low-cost setup. Leave `MLFLOW_TRACKING_URL` blank unless you intentionally add that service later.
