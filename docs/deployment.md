# Deployment

> **Start here for production:** [manual-setup.md](manual-setup.md) — complete step-by-step checklist for Vercel + Render + Neon + Upstash.

---

## Architectures

| Mode | When to use |
|------|-------------|
| **Free-tier split** | Vercel (frontend) + Render (API) + Neon + Upstash — default for MVP |
| **Docker Compose** | Self-hosted VPS with full search stack (OpenSearch, MinIO, SearXNG) |

---

## Free-tier split deploy (Vercel + Render)

### Architecture

```
Browser → Vercel (React SPA)
              ↓ JWT Bearer or X-API-Key
         Render API (credenceai-api)
              ↓              ↓
           Neon          Upstash
         (Postgres)       (Redis)
```

On Render **free tier**, background workers are not available. The blueprint sets `CELERY_ALWAYS_EAGER=true` so jobs run inline in the API process. Upgrade to a paid plan to run [`credenceai-worker`](../render.yaml) separately.

### Quick steps

| Step | Action | Doc section |
|------|--------|-------------|
| 1 | Create Neon + Upstash; copy URLs | [manual-setup.md § Phase 1](manual-setup.md#phase-1--databases) |
| 2 | Apply Render blueprint; set secrets | [manual-setup.md § Phase 2](manual-setup.md#phase-2--render-api-blueprint) |
| 3 | Deploy Vercel frontend; set `VITE_API_BASE_URL` | [manual-setup.md § Phase 3](manual-setup.md#phase-3--vercel-frontend) |
| 4 | Configure Google + GitHub OAuth | [manual-setup.md § Phase 4–5](manual-setup.md#phase-4--google-oauth) |
| 5 | Run verification checklist | [manual-setup.md § Phase 6](manual-setup.md#phase-6--full-deployment-verification) |

### Key files

| File | Purpose |
|------|---------|
| [`render.yaml`](../render.yaml) | Render Blueprint — API env defaults, CORS, OAuth redirect URIs |
| [`frontend/vercel.json`](../frontend/vercel.json) | Vercel build (SDK + SPA routing) |
| [`backend/.env.production.example`](../backend/.env.production.example) | All production env vars |
| [`scripts/render-env.template.env`](../scripts/render-env.template.env) | Copy-paste template for Render dashboard |
| [`scripts/verify-deployment.ps1`](../scripts/verify-deployment.ps1) | Post-deploy smoke test |

### Validate deployment

```bash
curl https://YOUR-API.onrender.com/api/health
curl https://YOUR-API.onrender.com/api/auth/github/url
curl https://YOUR-API.onrender.com/api/auth/google/url
```

```powershell
.\scripts\verify-deployment.ps1 -ApiUrl "https://YOUR-API.onrender.com"
```

After creating an API key in Settings:

```bash
curl -X POST https://YOUR-API.onrender.com/api/jobs \
  -H "X-API-Key: cred_sk_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"job_type":"search_query","query":"test","input":"test"}'
```

### Free-tier limitations

| Component | On free tier |
|-----------|--------------|
| OpenSearch, MinIO, SearXNG | Not deployed — search uses SQLite fallback + external APIs |
| Celery worker | Not available — `CELERY_ALWAYS_EAGER=true` on API |
| Render spin-down | Cold starts after ~15 min idle |

Acceptable for MVP. For full search stack, use Docker Compose on a VPS (below).

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
- `CELERY_ALWAYS_EAGER=false` (worker runs separately)
- `DATABASE_URL` → Postgres
- `JWT_SECRET` — `openssl rand -hex 32`
- `CORS_ALLOWED_ORIGINS` — frontend URL(s)
- `VITE_API_BASE_URL` — build arg for frontend image
- At least one OAuth provider (Google or GitHub)

---

## CI/CD

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) | Push/PR to `master`/`main` | Backend pytest, SDK + frontend build |
| [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) | Push to `master`/`main` | Render deploy hook + smoke tests |
| [`.github/workflows/backup.yml`](../.github/workflows/backup.yml) | Weekly cron | Postgres `pg_dump` artifact |
| [`.github/workflows/monitor.yml`](../.github/workflows/monitor.yml) | Every 6 hours | API health check |

**CI backend env** (no secrets required):

```yaml
APP_ENV: local
CELERY_ALWAYS_EAGER: "true"
DATABASE_URL: "sqlite:///:memory:"
PYTHONPATH: src
```

**GitHub repository secrets** (optional):

| Secret | Purpose |
|--------|---------|
| `RENDER_DEPLOY_HOOK_URL` | Auto-deploy API on push |
| `API_URL` | Smoke tests + monitoring |
| `DATABASE_URL` | Weekly backup workflow |
| `SMOKE_TEST_API_KEY` | Post-deploy API key test |

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

- **Neon free tier:** [`.github/workflows/backup.yml`](../.github/workflows/backup.yml) (weekly `pg_dump` artifacts)
- **VPS / Compose:** [`backend/scripts/backup_cron.example`](../backend/scripts/backup_cron.example)
- **Restore:** `psql "$DATABASE_URL" < backup.sql`

## Monitoring

1. Render health check on `/api/health`
2. GitHub Actions [`monitor.yml`](../.github/workflows/monitor.yml) (set `API_URL` secret)
3. [UptimeRobot](https://uptimerobot.com) for external uptime alerts

---

## Related docs

| Doc | Description |
|-----|-------------|
| [manual-setup.md](manual-setup.md) | **Complete production deploy checklist** |
| [oauth-setup.md](oauth-setup.md) | OAuth configuration and troubleshooting |
| [environment.md](environment.md) | Full environment variable reference |
| [operations.md](operations.md) | Day-2 operations |
