# Operations

## Health checks

| Endpoint | Purpose |
|----------|---------|
| `GET /api/health` | API liveness + dependency status |
| `GET /api/system/metrics` | System metrics |

Docker compose services include healthchecks for Postgres, Redis, MinIO, OpenSearch, and SearXNG.

## Logging

- Structured logging via `backend/src/app/logging_config.py`
- Level controlled by `LOG_LEVEL` env var
- Each request gets an `X-Trace-Id` header for correlation

## Common failures

### Port 8000 blocked (Windows)

If uvicorn fails with `WinError 10013`, choose another port (e.g. `8012`) and update `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8012/api
```

### Browser sign-in `Illegal invocation`

Fixed in SDK by binding `fetch` to `globalThis`. Rebuild frontend after SDK changes if using `file:../sdk`.

### CORS errors in browser

Set `CORS_ALLOWED_ORIGINS` to include your frontend origin (e.g. `http://localhost:3000`).

### 401 on `/api/jobs`

Jobs require JWT Bearer auth. Sign in via frontend or pass a valid token.

### OpenSearch / MinIO connection errors

- Run `docker compose up` for infra services, or
- Set `MOCK_SERVICES=true` for local dev without Docker

### Celery jobs not processing

- Ensure Redis is running
- Start worker: `celery -A app.worker.celery_app worker --loglevel=info`
- Or set `CELERY_ALWAYS_EAGER=true` for inline execution

### Google auth returns 503

In production, configure `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI`. Mock auth only works when `APP_ENV=local`.

### Alembic import errors

Run from `backend/` with `PYTHONPATH=src`.

## Monitoring recommendations

- Alert on `GET /api/health` non-200
- Track Celery queue depth via Redis
- Monitor OpenSearch cluster health
- Rotate `JWT_SECRET` and API keys on compromise

## Legacy ops dashboard

`GET /dashboard` on the backend provides an inline HTML control panel for operators when the React frontend is unavailable.
