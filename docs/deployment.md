# Deployment

## Split architecture

| Service | Port | Image |
|---------|------|-------|
| Backend API | 8000 | `backend/Dockerfile` |
| Frontend (nginx) | 3000 → 80 | `frontend/Dockerfile` |
| Celery worker | — | same as backend |
| Postgres, Redis, MinIO, OpenSearch, SearXNG | various | `backend/docker-compose.prod.yml` |

## Docker Compose (full stack)

```bash
cd backend
docker compose -f docker-compose.prod.yml up --build
```

Set production secrets via environment overrides or a `.env` file consumed by compose.

### Required production settings

- `APP_ENV=production`
- `MOCK_SERVICES=false`
- `DATABASE_URL` pointing to Postgres
- `JWT_SECRET` — strong random value
- `CORS_ALLOWED_ORIGINS` — your frontend URL(s)
- `VITE_API_BASE_URL` — build arg for frontend image

## Backend only

```bash
cd backend
docker build -t credenceai-api .
docker run -p 8000:8000 --env-file .env credenceai-api
```

## Frontend only

```bash
docker build -f frontend/Dockerfile \
  --build-arg VITE_API_BASE_URL=https://api.yourdomain.com/api \
  -t credenceai-frontend .
docker run -p 80:80 credenceai-frontend
```

## SDK release

Publish from `sdk/` to npm. See [sdk.md](sdk.md).

## Infra services

`backend/docker-compose.yml` runs infrastructure only (no app) for local development:

```bash
cd backend
docker compose up -d
```

Then run the API and worker on the host with `MOCK_SERVICES=false`.
