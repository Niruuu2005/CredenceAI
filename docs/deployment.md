# Deployment

## Architectures

| Mode | When to use |
|------|-------------|
| **Free-tier split** | Vercel (frontend) + Render (API/worker) + Neon + Upstash |
| **Docker Compose** | Self-hosted VPS with full search stack |

---

## Free-tier split deploy (Vercel + Render)

### 1. Managed services

| Service | Provider | Notes |
|---------|----------|-------|
| Frontend | [Vercel](https://vercel.com) | Root directory: `frontend` |
| API + Celery | [Render](https://render.com) | Blueprint: [`render.yaml`](../render.yaml) |
| Postgres | [Neon](https://neon.tech) | Copy `DATABASE_URL` |
| Redis | [Upstash](https://upstash.com) | Copy `REDIS_URL` (`rediss://...`) |

### 2. Deploy backend (Render)

1. Connect GitHub repo to Render.
2. Apply blueprint from `render.yaml` or create two Docker services from `backend/Dockerfile`.
3. Set environment variables (see [`backend/.env.production.example`](../backend/.env.production.example)):
   - `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`
   - `ENABLE_API_KEY_AUTH=true`
   - `GOOGLE_*` and/or `GITHUB_*` OAuth vars
   - `CORS_ALLOWED_ORIGINS=["https://YOUR-APP.vercel.app"]`
4. Health check path: `/api/health`
5. Worker command: `celery -A app.worker worker --loglevel=info`

### 3. Deploy frontend (Vercel)

1. Import repo; set **Root Directory** to `frontend`.
2. Environment variable:
   ```
   VITE_API_BASE_URL=https://YOUR-API.onrender.com/api
   ```
3. [`frontend/vercel.json`](../frontend/vercel.json) builds the local SDK and enables SPA routing.

### 4. OAuth setup

Follow **[manual-setup.md](manual-setup.md)** (full checklist) or **[oauth-setup.md](oauth-setup.md)** (OAuth detail only).

### 5. Validate deployment

```bash
# Health
curl https://YOUR-API.onrender.com/api/health

# After sign-in and creating an API key in Settings:
curl -X POST https://YOUR-API.onrender.com/api/jobs \
  -H "X-API-Key: cred_sk_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"job_type":"search_query","query":"test","input":"test"}'
```

### Free-tier limitations

Without OpenSearch, MinIO, and SearXNG, search runs in **degraded mode** (SQLite index, local/ephemeral storage). Acceptable for MVP; add full stack via Docker Compose on a VPS when scaling.

---

## Docker Compose (full stack)

| Service | Port | Image |
|---------|------|-------|
| Backend API | 8000 | `backend/Dockerfile` |
| Frontend (nginx) | 3000 → 80 | `frontend/Dockerfile` |
| Celery worker | — | same as backend |
| Postgres, Redis, MinIO, OpenSearch, SearXNG | various | `backend/docker-compose.prod.yml` |

```bash
cd backend
cp .env.production.example .env
# Edit .env with real secrets
docker compose -f docker-compose.prod.yml --env-file .env up --build
```

### Required production settings

- `APP_ENV=production`
- `MOCK_SERVICES=false`
- `ENABLE_API_KEY_AUTH=true`
- `DATABASE_URL` → Postgres
- `JWT_SECRET` — strong random (`openssl rand -hex 32`)
- `CORS_ALLOWED_ORIGINS` — frontend URL(s)
- `VITE_API_BASE_URL` — build arg for frontend image
- At least one OAuth provider (Google or GitHub)

---

## CI/CD

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) | Push/PR | Tests + builds |
| [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) | Push to main | Render deploy hook + smoke tests |
| [`.github/workflows/backup.yml`](../.github/workflows/backup.yml) | Weekly cron | Postgres `pg_dump` artifact |
| [`.github/workflows/monitor.yml`](../.github/workflows/monitor.yml) | Every 6 hours | API health check |

**GitHub repository secrets:**

| Secret | Purpose |
|--------|---------|
| `RENDER_DEPLOY_HOOK_URL` | Auto-deploy API on push to main |
| `API_URL` | Smoke tests + monitoring (`https://your-api.onrender.com`) |
| `DATABASE_URL` | Weekly backup workflow |
| `SMOKE_TEST_API_KEY` | Optional post-deploy API key test |

Vercel deploys automatically via Git integration.

---

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

## Infra services (local dev)

`backend/docker-compose.yml` runs infrastructure only (no app):

```bash
cd backend
docker compose up -d
```

Then run the API and worker on the host with `MOCK_SERVICES=false`.

## Backups

- **Neon free tier:** use [`.github/workflows/backup.yml`](../.github/workflows/backup.yml) (weekly `pg_dump` artifacts).
- **VPS / Compose:** cron example in [`backend/scripts/backup_cron.example`](../backend/scripts/backup_cron.example).
- **Restore:** `psql "$DATABASE_URL" < backup.sql`

## Monitoring

1. Render health check on `/api/health`
2. GitHub Actions [`monitor.yml`](../.github/workflows/monitor.yml) (set `API_URL` secret)
3. [UptimeRobot](https://uptimerobot.com) (free) for external uptime alerts
