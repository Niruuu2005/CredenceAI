# Backend

See [backend/README.md](../backend/README.md) for commands.

## Stack

- FastAPI + Uvicorn
- SQLAlchemy + Alembic
- Celery + Redis
- OpenSearch (SQLite fallback)
- MinIO (local filesystem fallback)

## Environment

Copy `backend/.env.example` to `backend/.env`. Key variables:

| Variable | Purpose |
|----------|---------|
| `APP_ENV` | `local` or `production` |
| `DATABASE_URL` | SQLAlchemy connection string |
| `REDIS_URL` | Celery broker |
| `MOCK_SERVICES` | Dev fallback when external services unavailable |
| `CELERY_ALWAYS_EAGER` | Run tasks inline (local dev) |
| `CORS_ALLOWED_ORIGINS` | JSON list of allowed frontend origins |
| `JWT_SECRET` | JWT signing key |
| `GOOGLE_CLIENT_*` | Google OAuth |
| `DEV_LOGIN_*` | Local-only developer login |

Full list: [environment.md](environment.md)

## Migrations

```bash
cd backend
set PYTHONPATH=src
alembic upgrade head
alembic revision --autogenerate -m "description"
```

Migrations live in `backend/migrations/versions/`.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/browser_e2e_tests.py` | HTTP E2E suite |
| `scripts/verify_realtime_e2e.py` | Realtime pipeline check |
| `scripts/check_realtime.py` | Quick job/search smoke test |

Set `CREDENCEAI_BASE_URL` (default `http://localhost:8000`).

## Legacy dashboard

`GET /dashboard` serves inline HTML ops UI from `backend/src/app/templates/dashboard.html`.
