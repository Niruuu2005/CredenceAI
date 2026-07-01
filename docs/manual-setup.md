# Complete Production Deployment Guide

End-to-end checklist to deploy CredenceAI on the **free-tier split stack**: Vercel (frontend) + Render (API) + Neon (Postgres) + Upstash (Redis).

Use this document in order. Check off each step. Estimated time: **45–90 minutes** for a first deploy.

> **Related docs:** [deployment.md](deployment.md) (architecture overview), [oauth-setup.md](oauth-setup.md) (OAuth troubleshooting), [environment.md](environment.md) (full variable reference)

---

## What you are building

```mermaid
flowchart TB
  subgraph users [Users]
    Browser[Browser / SDK clients]
  end
  subgraph vercel [Vercel]
    SPA[React SPA]
  end
  subgraph render [Render]
    API[credenceai-api Web Service]
    Worker[credenceai-worker optional]
  end
  subgraph data [Managed data]
    Neon[(Neon Postgres)]
    Upstash[(Upstash Redis)]
  end
  subgraph oauth [OAuth providers]
    Google[Google Cloud OAuth]
    GitHub[GitHub OAuth App]
  end
  Browser --> SPA
  SPA -->|"JWT Bearer or API key"| API
  API --> Neon
  API --> Upstash
  Worker -.->|"paid plan only"| Neon
  Worker -.-> Upstash
  Google --> SPA
  GitHub --> SPA
  API --> Google
  API --> GitHub
```

| Component | Provider | Repo config |
|-----------|----------|-------------|
| Frontend | Vercel | [`frontend/vercel.json`](../frontend/vercel.json) |
| API | Render | [`render.yaml`](../render.yaml) |
| Database | Neon | `DATABASE_URL` on Render |
| Cache / Celery broker | Upstash | `REDIS_URL` on Render |
| CI | GitHub Actions | [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) |

**Write your URLs here once deployed:**

```
FRONTEND_URL=https://________________.vercel.app
FRONTEND_ALIAS=https://________________.vercel.app   # optional Vercel alias
API_URL=https://________________.onrender.com
```

---

## Before you start

### Accounts (all have free tiers)

- [GitHub](https://github.com) — source repo + Actions
- [Neon](https://neon.tech) — Postgres
- [Upstash](https://upstash.com) — Redis
- [Render](https://render.com) — API hosting
- [Vercel](https://vercel.com) — frontend hosting
- [Google Cloud](https://console.cloud.google.com) — Google sign-in (optional but recommended)
- GitHub OAuth App — GitHub sign-in (optional but recommended; **at least one OAuth provider is required**)

### Security rules

- **Never** commit secrets to git (`.env`, connection strings, OAuth secrets).
- **Never** paste secrets in chat, screenshots, or public issues.
- Set secrets only in provider dashboards (Render, Vercel, GitHub Actions Secrets).
- If a secret is exposed, **rotate it immediately** (see [Security rotation](#security-rotation-after-exposure)).

### Auth model (important)

Production runs with `ENABLE_API_KEY_AUTH=true`:

| Client | How it authenticates |
|--------|----------------------|
| **Web UI** (after OAuth sign-in) | `Authorization: Bearer <JWT>` stored in browser |
| **Scripts / SDK / curl** | `X-API-Key: cred_sk_...` from Settings → Create API Key |

The dashboard **must** accept JWT Bearer tokens. If you see `X-API-Key header is required` after sign-in, the API is on an old build — redeploy from latest `master`.

---

## Phase 1 — Databases

### 1.1 Neon (Postgres)

1. Sign up at [neon.tech](https://neon.tech).
2. Create a project (e.g. `credenceai`).
3. Copy the **connection string** (starts with `postgresql://`, includes `?sslmode=require`).
4. Save as `DATABASE_URL` — you will paste this into Render in Phase 2.

- [ ] `DATABASE_URL` copied and stored in a password manager

### 1.2 Upstash (Redis)

1. Sign up at [upstash.com](https://upstash.com).
2. Create a Redis database in a region **close to your Render region** (e.g. US East).
3. Copy the **Redis URL** (`rediss://default:...@...:6379`).
4. Save as `REDIS_URL`.

- [ ] `REDIS_URL` copied and stored in a password manager

---

## Phase 2 — Render API (Blueprint)

### 2.1 Connect GitHub and create Blueprint

1. Sign up at [render.com](https://render.com).
2. **Dashboard → New → Blueprint**.
3. Connect the CredenceAI GitHub repository.
4. Render reads [`render.yaml`](../render.yaml) at the repo root and creates:
   - **Web service:** `credenceai-api` (Docker, health check `/api/health`)
   - **Background worker:** `credenceai-worker` (only if your plan supports workers)

- [ ] Blueprint created and linked to repo

### 2.2 Update `render.yaml` for your frontend URLs

Before the first successful OAuth deploy, edit [`render.yaml`](../render.yaml) in your repo (or after deploy, sync the blueprint) so these match **your** Vercel URLs:

```yaml
GOOGLE_REDIRECT_URI:
  value: https://YOUR-FRONTEND.vercel.app/auth/google/callback
GITHUB_REDIRECT_URI:
  value: https://YOUR-FRONTEND.vercel.app/auth/github/callback
CORS_ALLOWED_ORIGINS:
  value: '["https://YOUR-FRONTEND.vercel.app","https://YOUR-ALIAS.vercel.app"]'
```

Rules:

- **No trailing slashes** on origins.
- Include **every** Vercel URL users might open (production URL + any alias).
- Pick **one** canonical URL for OAuth redirect URIs (GitHub allows only one callback per OAuth app).

Push to `master` and **Sync Blueprint** in Render if you change these values.

- [ ] `render.yaml` URLs updated for my Vercel app
- [ ] Blueprint synced after push

### 2.3 Set secrets on `credenceai-api`

Open **Render → credenceai-api → Environment**.

#### Set manually (dashboard only — `sync: false` in blueprint)

| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | Neon connection string | From Phase 1.1 |
| `REDIS_URL` | Upstash `rediss://...` URL | From Phase 1.2 |
| `GOOGLE_CLIENT_ID` | From Google Console | Phase 4 |
| `GOOGLE_CLIENT_SECRET` | From Google Console | Phase 4 |
| `GITHUB_CLIENT_ID` | From GitHub OAuth App | Phase 5 |
| `GITHUB_CLIENT_SECRET` | From GitHub OAuth App | Phase 5 |

#### Already set by blueprint (verify, do not wipe)

| Variable | Typical value |
|----------|---------------|
| `APP_ENV` | `production` |
| `MOCK_SERVICES` | `false` |
| `ENABLE_API_KEY_AUTH` | `true` |
| `RATE_LIMIT_ENABLED` | `true` |
| `CELERY_ALWAYS_EAGER` | `true` on **free tier** (see below) |
| `JWT_SECRET` | Auto-generated by Render |
| `GOOGLE_REDIRECT_URI` | Your Vercel `/auth/google/callback` |
| `GITHUB_REDIRECT_URI` | Your Vercel `/auth/github/callback` |
| `CORS_ALLOWED_ORIGINS` | JSON array of Vercel origins |

> **Warning when editing env vars:** Render secret fields often show blank in the UI. Saving the form with empty secret fields can **wipe** existing values. Only add or update the specific variables you intend to change.

- [ ] `DATABASE_URL` set on Render
- [ ] `REDIS_URL` set on Render
- [ ] At least one OAuth provider configured (Google and/or GitHub)

### 2.4 Free tier vs paid tier (Celery worker)

| Plan | `CELERY_ALWAYS_EAGER` | Worker service |
|------|----------------------|----------------|
| **Render free** | `true` on API — jobs run **inline** in the web process | **Cannot** create `credenceai-worker` (plan blocks background workers) |
| **Render paid ($7+/mo)** | Set `false` on API | Sync blueprint → worker runs `celery -A app.worker worker --loglevel=info` |

On free tier this is expected and fine for MVP. Jobs still work; they block the API request until complete.

- [ ] Understood: free tier uses inline jobs (`CELERY_ALWAYS_EAGER=true`)

### 2.5 First API deploy

1. **Manual Deploy** (or wait for auto-deploy from GitHub).
2. Wait for build to finish (Docker build + Alembic migrations on startup).
3. Copy your service URL → `API_URL` (e.g. `https://credenceai-api.onrender.com`).

**Smoke test:**

```bash
curl https://YOUR-API.onrender.com/api/health
```

Expected: `"overall":"online"` (first request after idle may take 30–60s on free tier).

PowerShell helper:

```powershell
.\scripts\verify-deployment.ps1 -ApiUrl "https://YOUR-API.onrender.com"
```

- [ ] API health returns `online`
- [ ] `API_URL` recorded

---

## Phase 3 — Vercel frontend

### 3.1 Import project

1. Sign up at [vercel.com](https://vercel.com).
2. **Add New → Project** → import the same GitHub repo.
3. **Root Directory:** `frontend`
4. Framework preset: Vite (auto-detected).
5. Build settings come from [`frontend/vercel.json`](../frontend/vercel.json):
   - Installs and builds the local SDK first
   - Uses `npm install` (not `npm ci`) for cross-platform lockfile compatibility

- [ ] Vercel project created with root `frontend`

### 3.2 Environment variable (required)

**Settings → Environment Variables:**

| Name | Value | Environments |
|------|-------|--------------|
| `VITE_API_BASE_URL` | `https://YOUR-FRONTEND.vercel.app/api` | Production (+ Preview if desired) |

Use your **Vercel frontend URL** (not the Render URL). [`vercel.json`](../frontend/vercel.json) rewrites `/api/*` to Render server-side, so the browser stays same-origin and avoids CORS.

```env
VITE_API_BASE_URL=https://credence-ai-gamma.vercel.app/api
```

Do **not** set this to `https://credenceai-api.onrender.com/api` — that causes cross-origin calls and CORS / cold-start failures.

If you already have the Render URL set, deploy the latest frontend code: it auto-uses the `/api` proxy on `*.vercel.app` hosts even when the env var points at Render.

- [ ] `VITE_API_BASE_URL` set for Production

### 3.3 Deploy and record URL

1. **Deployments → Redeploy** (required after adding env vars — Vite bakes them at build time).
2. Copy the production URL → `FRONTEND_URL`.
3. If Vercel assigned an alias (e.g. `your-app.vercel.app`), record it as `FRONTEND_ALIAS`.

- [ ] Frontend loads at `FRONTEND_URL`
- [ ] Sign-in page opens: `FRONTEND_URL/auth/sign-in`

---

## Phase 4 — Google OAuth

Detailed troubleshooting: [oauth-setup.md#google-oauth](oauth-setup.md#google-oauth)

### 4.1 Google Cloud project

1. [Google Cloud Console](https://console.cloud.google.com/) → create or select a project.
2. **APIs & Services → OAuth consent screen**
   - User type: **External** (public) or **Internal** (Workspace)
   - App name, support email, developer contact
   - Scopes: `openid`, `email`, `profile`
   - **Testing mode:** add your Gmail under **Test users**
   - **Publish app** when ready for anyone to sign in

### 4.2 OAuth 2.0 Client ID

**APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID → Web application**

**Authorized JavaScript origins** (no trailing slash):

```
https://YOUR-FRONTEND.vercel.app
https://YOUR-ALIAS.vercel.app          # if you use an alias
http://localhost:3000                  # optional, local dev
```

**Authorized redirect URIs** (must match **exactly**):

```
https://YOUR-FRONTEND.vercel.app/auth/google/callback
https://YOUR-ALIAS.vercel.app/auth/google/callback   # if needed
http://localhost:3000/auth/google/callback           # optional
```

Copy **Client ID** and **Client Secret**.

### 4.3 Render env vars

```env
GOOGLE_CLIENT_ID=<from Google Console>
GOOGLE_CLIENT_SECRET=<from Google Console>
GOOGLE_REDIRECT_URI=https://YOUR-FRONTEND.vercel.app/auth/google/callback
```

If `GOOGLE_REDIRECT_URI` is blueprint-managed, update [`render.yaml`](../render.yaml) instead of the dashboard, then sync blueprint.

- [ ] Google OAuth client created
- [ ] Consent screen configured (test users or published)
- [ ] `GOOGLE_*` vars on Render
- [ ] API redeployed

### 4.4 Verify Google sign-in

```bash
curl https://YOUR-API.onrender.com/api/auth/google/url
```

Expected: `"mock": false` and a Google OAuth URL.

Browser:

1. Open `FRONTEND_URL/auth/sign-in`
2. Click **Google** → Google account chooser → authorize
3. Land on `/app/dashboard`

| Error | Fix |
|-------|-----|
| `redirect_uri_mismatch` | Google Console redirect URI must exactly match `GOOGLE_REDIRECT_URI` |
| `503 Google OAuth not configured` | Set all three `GOOGLE_*` on Render; redeploy |
| `access_denied` / app not verified | Add yourself as test user or publish consent screen |
| CORS error | Set `VITE_API_BASE_URL=https://YOUR-FRONTEND.vercel.app/api` on Vercel (not Render URL) and redeploy |

- [ ] Google sign-in reaches dashboard

---

## Phase 5 — GitHub OAuth

Detailed troubleshooting: [oauth-setup.md#github-oauth](oauth-setup.md#github-oauth)

### 5.1 GitHub OAuth App

**GitHub → Settings → Developer settings → OAuth Apps → New OAuth App**

| Field | Value |
|-------|-------|
| Application name | CredenceAI |
| Homepage URL | `https://YOUR-FRONTEND.vercel.app` |
| Authorization callback URL | `https://YOUR-FRONTEND.vercel.app/auth/github/callback` |

> GitHub allows **one** callback URL per app. If users bookmark an alias URL, either redirect them to the canonical frontend or create a second OAuth app for the alias.

Copy **Client ID** → generate **Client Secret**.

### 5.2 Render env vars

```env
GITHUB_CLIENT_ID=<from GitHub>
GITHUB_CLIENT_SECRET=<from GitHub>
GITHUB_REDIRECT_URI=https://YOUR-FRONTEND.vercel.app/auth/github/callback
```

- [ ] GitHub OAuth app created
- [ ] `GITHUB_*` vars on Render
- [ ] API redeployed

### 5.3 Verify GitHub sign-in

```bash
curl https://YOUR-API.onrender.com/api/auth/github/url
```

Expected: `"mock": false` and `redirect_uri` pointing at your Vercel callback.

Browser: **GitHub** on sign-in page → authorize → `/app/dashboard`.

| Error | Fix |
|-------|-----|
| Redirect URI not associated | GitHub app callback must match `GITHUB_REDIRECT_URI` |
| `incorrect_client_credentials` | Regenerate client secret; update Render |
| `X-API-Key header is required` on dashboard | Redeploy API from latest `master` (JWT middleware fix) |
| Missing email | Grant email scope on GitHub; set primary email |

- [ ] GitHub sign-in reaches dashboard
- [ ] Dashboard pages load (jobs, monitors, settings) without auth errors

---

## Phase 6 — Full deployment verification

Run every check before calling the deploy complete.

### 6.1 API checks

```bash
# Health
curl https://YOUR-API.onrender.com/api/health

# OAuth configured (non-mock)
curl https://YOUR-API.onrender.com/api/auth/google/url
curl https://YOUR-API.onrender.com/api/auth/github/url
```

- [ ] Health `overall: online`
- [ ] Google URL `mock: false`
- [ ] GitHub URL `mock: false` with correct `redirect_uri`

### 6.2 Frontend checks

- [ ] `FRONTEND_URL/auth/sign-in` loads (HTTP 200)
- [ ] `FRONTEND_ALIAS/auth/sign-in` loads if using alias
- [ ] Google sign-in → dashboard
- [ ] GitHub sign-in → dashboard
- [ ] Navigate to Monitors / Jobs — no `X-API-Key` errors

### 6.3 API key flow (programmatic access)

1. Sign in via OAuth.
2. **Settings → Create API Key** → copy `cred_sk_...` (shown once).

```bash
# Validate key
curl https://YOUR-API.onrender.com/api/auth/validate \
  -H "X-API-Key: cred_sk_YOUR_KEY"

# Submit a job
curl -X POST https://YOUR-API.onrender.com/api/jobs \
  -H "X-API-Key: cred_sk_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"job_type":"search_query","query":"test","input":"test"}'
```

PowerShell with API key:

```powershell
.\scripts\verify-deployment.ps1 -ApiUrl "https://YOUR-API.onrender.com" -ApiKey "cred_sk_YOUR_KEY"
```

- [ ] API key validates
- [ ] Job submit returns `202`
- [ ] Revoked key returns `401`

---

## Phase 7 — GitHub Actions (optional automation)

Repo → **Settings → Secrets and variables → Actions**

| Secret | Required? | Purpose |
|--------|-----------|---------|
| `RENDER_DEPLOY_HOOK_URL` | Optional | Trigger API redeploy on push ([`deploy.yml`](../.github/workflows/deploy.yml)) |
| `API_URL` | Optional | Smoke tests + [`monitor.yml`](../.github/workflows/monitor.yml) |
| `DATABASE_URL` | Optional | Weekly [`backup.yml`](../.github/workflows/backup.yml) |
| `SMOKE_TEST_API_KEY` | Optional | Post-deploy job test in `deploy.yml` |

**Get deploy hook:** Render → credenceai-api → Settings → Deploy Hook → copy URL.

Vercel deploys automatically via Git integration — no GitHub secret needed for frontend.

CI on push (tests only — no secrets required):

- Backend: `pytest` with SQLite (`DATABASE_URL=sqlite:///:memory:`)
- SDK + frontend: build and lint

- [ ] CI badge green on `master` (optional)
- [ ] Deploy/monitor secrets added if desired

---

## Phase 8 — Monitoring and backups (optional)

### UptimeRobot (free)

1. [uptimerobot.com](https://uptimerobot.com) → HTTP monitor
2. URL: `https://YOUR-API.onrender.com/api/health`
3. Alert email

### Render health check

Confirm path is `/api/health` (set in blueprint).

### Database backups

- Set `DATABASE_URL` as GitHub Actions secret → weekly [`backup.yml`](../.github/workflows/backup.yml) artifacts
- Or cron [`backend/scripts/backup_postgres.sh`](../backend/scripts/backup_postgres.sh) on a VPS

- [ ] External uptime monitor configured (optional)
- [ ] Backup strategy chosen (optional)

---

## Phase 9 — Custom domain (when ready)

1. DNS: `app.yourdomain.com` → Vercel, `api.yourdomain.com` → Render
2. Update **Google** JavaScript origins + redirect URIs
3. Update **GitHub** homepage + callback URL
4. Update Render: `GOOGLE_REDIRECT_URI`, `GITHUB_REDIRECT_URI`, `CORS_ALLOWED_ORIGINS`
5. Update Vercel: `VITE_API_BASE_URL=https://api.yourdomain.com/api`
6. Redeploy frontend + API; sync blueprint

---

## Phase 10 — Upgrade to background worker (paid Render)

When you outgrow inline job processing:

1. Upgrade Render plan (worker services require paid tier).
2. Sync blueprint — creates `credenceai-worker`.
3. On **credenceai-api**, set `CELERY_ALWAYS_EAGER=false`.
4. Redeploy API and worker.
5. Verify a job runs without blocking the HTTP request.

---

## Quick reference — all environment variables

### Render (`credenceai-api`)

Template: [`scripts/render-env.template.env`](../scripts/render-env.template.env)  
Full reference: [`backend/.env.production.example`](../backend/.env.production.example)

```env
# Core (blueprint defaults shown)
APP_ENV=production
MOCK_SERVICES=false
CELERY_ALWAYS_EAGER=true          # false when worker is running on paid plan
RATE_LIMIT_ENABLED=true
ENABLE_API_KEY_AUTH=true

# Secrets (dashboard)
DATABASE_URL=postgresql://...
REDIS_URL=rediss://...
JWT_SECRET=<auto or openssl rand -hex 32>

# OAuth (dashboard + blueprint redirect URIs)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://YOUR-FRONTEND.vercel.app/auth/google/callback
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GITHUB_REDIRECT_URI=https://YOUR-FRONTEND.vercel.app/auth/github/callback

# CORS (blueprint or dashboard) — JSON array, no trailing slashes
CORS_ALLOWED_ORIGINS=["https://YOUR-FRONTEND.vercel.app","https://YOUR-ALIAS.vercel.app"]
```

### Vercel

```env
VITE_API_BASE_URL=https://YOUR-FRONTEND.vercel.app/api
```

### Stripe (optional — billing)

```env
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...
STRIPE_PRICE_ID_PRO=...
STRIPE_PRICE_ID_ENTERPRISE=...
STRIPE_SUCCESS_URL=https://YOUR-FRONTEND.vercel.app/app/billing?success=1
STRIPE_CANCEL_URL=https://YOUR-FRONTEND.vercel.app/app/billing?canceled=1
```

---

## Security rotation (after exposure)

If any secret was pasted in chat, logs, or a screenshot:

| Secret | Rotate at | Then update on Render |
|--------|-----------|----------------------|
| `DATABASE_URL` | Neon → Reset password | credenceai-api env → Manual Deploy |
| `REDIS_URL` | Upstash → Reset credentials | credenceai-api env → Manual Deploy |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App → Regenerate | credenceai-api env → Manual Deploy |
| `GOOGLE_CLIENT_SECRET` | GCP Credentials → Reset secret | credenceai-api env → Manual Deploy |
| `JWT_SECRET` | Generate new (`openssl rand -hex 32`) | All users must sign in again |

Pre-commit check (local):

```powershell
.\scripts\check-secrets-not-committed.ps1
```

---

## Known limitations (free tier)

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| No OpenSearch / MinIO / SearXNG on Render | Search runs in **degraded mode** (SQLite index, provider fallbacks) | Use Docker Compose on a VPS for full stack — [deployment.md](deployment.md) |
| Render spin-down | First request after idle is slow (30–60s) | UptimeRobot ping; upgrade plan |
| Inline Celery (`CELERY_ALWAYS_EAGER=true`) | Long jobs block API responses | Upgrade Render + enable worker |
| Neon / Upstash quotas | Connection and storage limits | Monitor dashboards; upgrade when needed |
| GitHub one callback URL | Alias URL sign-in may redirect to canonical host | Pick one canonical `FRONTEND_URL` |

---

## Troubleshooting index

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| API won't start in production | Missing OAuth vars | Set Google and/or GitHub credentials |
| `redirect_uri_mismatch` | Google URI mismatch | Align GCP client + `GOOGLE_REDIRECT_URI` |
| GitHub redirect error | Callback mismatch | Align GitHub app + `GITHUB_REDIRECT_URI` |
| CORS error in browser | `VITE_API_BASE_URL` points at Render instead of Vercel | Set `https://YOUR-FRONTEND.vercel.app/api` and redeploy |
| `X-API-Key` after sign-in | Old API build | Deploy latest `master` |
| Frontend calls wrong API | Wrong `VITE_API_BASE_URL` | Use your Vercel URL + `/api`, not Render; **redeploy** |
| Jobs never complete (paid) | Worker not running | Create worker; `CELERY_ALWAYS_EAGER=false` |
| Jobs slow but work (free) | Inline processing | Expected on free tier |
| Blueprint overwrote my env | Sync from `render.yaml` | Use `sync: false` for secrets; pin URLs in yaml |
| CI fails on pytest | Missing `PYTHONPATH` / SQLite | See [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) |

---

## Deploy complete checklist

Copy this block and check everything off:

```
[ ] Neon DATABASE_URL on Render
[ ] Upstash REDIS_URL on Render
[ ] Render API health online
[ ] Vercel VITE_API_BASE_URL set and redeployed
[ ] render.yaml URLs match my Vercel app
[ ] Google OAuth: console + Render + sign-in works
[ ] GitHub OAuth: app + Render + sign-in works
[ ] Dashboard loads without X-API-Key errors
[ ] API key created and curl job test passes
[ ] Secrets not committed to git
[ ] (Optional) CI secrets, monitoring, backups configured
```

When all required items are checked, production deploy is **100% complete**.

---

## Related docs

| Doc | Contents |
|-----|----------|
| [deployment.md](deployment.md) | Architecture, Docker Compose, CI/CD overview |
| [oauth-setup.md](oauth-setup.md) | OAuth-only reference and errors |
| [environment.md](environment.md) | Full variable reference |
| [operations.md](operations.md) | Day-2 operations |
| [backend/.env.production.example](../backend/.env.production.example) | Production env template |
