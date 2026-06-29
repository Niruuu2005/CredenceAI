# CredenceAI Backend

FastAPI search-intelligence API, Celery workers, Alembic migrations, and legacy ops dashboard.

## Prerequisites

- Python 3.11+
- (Optional) Docker for Postgres, Redis, MinIO, OpenSearch, SearXNG

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
cp .env.example .env            # edit values as needed
```

## Database migrations

```bash
cd backend
set PYTHONPATH=src               # Windows
# export PYTHONPATH=src          # macOS/Linux
alembic upgrade head
```

## Run API

```bash
cd backend
set PYTHONPATH=src
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Windows port note:** If you see `WinError 10013` on port 8000, use `--port 8012` and point the frontend at `VITE_API_BASE_URL=http://localhost:8012/api`.

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health
- Legacy ops dashboard: http://localhost:8000/dashboard

## Run Celery worker

```bash
cd backend
set PYTHONPATH=src
celery -A app.worker.celery_app worker --loglevel=info
```

## Tests

```bash
cd backend
python -m pytest
```

## Docker (full stack)

```bash
cd backend
docker compose -f docker-compose.prod.yml up --build
```

Backend API: port `8000`. Frontend (separate container): port `3000`.

## Layout

| Path | Purpose |
|------|---------|
| `src/app/` | FastAPI application package |
| `src/app/api/` | REST route modules |
| `src/app/services/` | Business logic and integrations |
| `migrations/` | Alembic database migrations |
| `tests/` | Pytest suite |
| `scripts/` | E2E and verification utilities |

See [../docs/backend.md](../docs/backend.md) for full environment variable reference.
