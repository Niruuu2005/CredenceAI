# Manual Setup Checklist

Everything in this document must be done **by you** in external dashboards (Vercel, Render, Neon, Google, GitHub, etc.). The codebase and CI workflows are already prepared; they cannot complete these steps for you.

Use this order. Check off each item as you go.

**Write down your URLs once deployed:**

```
FRONTEND_URL=https://________________.vercel.app
API_URL=https://________________.onrender.com
```

---

## Phase 1 — Create accounts and databases

### 1.1 Neon (Postgres)

- [ ] Sign up at [neon.tech](https://neon.tech)
- [ ] Create a project and database named `credenceai`
- [ ] Copy the **connection string** → this is `DATABASE_URL`
- [ ] Keep it secret; never commit it to git

### 1.2 Upstash (Redis)

- [ ] Sign up at [upstash.com](https://upstash.com)
- [ ] Create a Redis database (any region close to Render)
- [ ] Copy the **Redis URL** (`rediss://...`) → this is `REDIS_URL`

### 1.3 Render (API + worker)

- [ ] Sign up at [render.com](https://render.com)
- [ ] Connect your GitHub repository
- [ ] Create a **Blueprint** from [`render.yaml`](../render.yaml) in the repo root  
  — or manually create two **Docker** services from `backend/Dockerfile`:
  - **Web service** `credenceai-api` — port 8000, health check `/api/health`
  - **Background worker** `credenceai-worker` — command:  
    `celery -A app.worker worker --loglevel=info`
- [ ] Note your API URL after first deploy → `API_URL`

### 1.4 Vercel (frontend)

- [ ] Sign up at [vercel.com](https://vercel.com)
- [ ] Import the same GitHub repository
- [ ] Set **Root Directory** to `frontend`
- [ ] Deploy (build uses [`frontend/vercel.json`](../frontend/vercel.json))
- [ ] Note your frontend URL → `FRONTEND_URL`

---

## Phase 2 — Configure Render (API + worker)

Open the **credenceai-api** service → **Environment** and set:

### Required

| Variable | Value | How to get it |
|----------|-------|---------------|
| `APP_ENV` | `production` | — |
| `MOCK_SERVICES` | `false` | — |
| `CELERY_ALWAYS_EAGER` | `false` | — |
| `RATE_LIMIT_ENABLED` | `true` | — |
| `ENABLE_API_KEY_AUTH` | `true` | — |
| `DATABASE_URL` | Neon connection string | Phase 1.1 |
| `REDIS_URL` | Upstash URL | Phase 1.2 |
| `JWT_SECRET` | 64+ random characters | `openssl rand -hex 32` |
| `CORS_ALLOWED_ORIGINS` | `["FRONTEND_URL"]` | No trailing slash on URL |

Example:

```env
CORS_ALLOWED_ORIGINS=["https://your-app.vercel.app"]
```

### OAuth (at least one provider required)

Set **Google** and/or **GitHub** vars in Phase 3. Until then, the API will not start in production.

### Optional (billing later)

| Variable | Purpose |
|----------|---------|
| `STRIPE_SECRET_KEY` | Stripe API |
| `STRIPE_WEBHOOK_SECRET` | Webhook verification |
| `STRIPE_PRICE_ID_PRO` | Pro plan price |
| `STRIPE_PRICE_ID_ENTERPRISE` | Enterprise plan price |
| `STRIPE_SUCCESS_URL` | `FRONTEND_URL/app/billing?success=1` |
| `STRIPE_CANCEL_URL` | `FRONTEND_URL/app/billing?canceled=1` |

- [ ] Set all required variables on **credenceai-api**
- [ ] Ensure **credenceai-worker** shares `DATABASE_URL` and `REDIS_URL` (Render blueprint links these automatically)
- [ ] **Redeploy** the API service after saving env vars

---

## Phase 3 — Configure Vercel (frontend)

In the Vercel project → **Settings** → **Environment Variables**:

| Variable | Value |
|----------|-------|
| `VITE_API_BASE_URL` | `API_URL/api` |

Example:

```env
VITE_API_BASE_URL=https://your-api.onrender.com/api
```

- [ ] Set `VITE_API_BASE_URL` for Production (and Preview if you want)
- [ ] **Redeploy** the frontend so the build picks up the variable

---

## Phase 4 — Google OAuth

Detailed reference: [oauth-setup.md](oauth-setup.md#google-oauth)

### 4.1 Google Cloud Console

- [ ] Go to [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services** → **Credentials**
- [ ] Create **OAuth 2.0 Client ID** → type **Web application**
- [ ] **Authorized JavaScript origins:**
  - `FRONTEND_URL`
  - `http://localhost:3000` (optional, for local dev)
- [ ] **Authorized redirect URIs** (must match **exactly**):
  - `FRONTEND_URL/auth/google/callback`
  - `http://localhost:3000/auth/google/callback` (optional)
- [ ] Copy **Client ID** and **Client Secret**

### 4.2 OAuth consent screen

- [ ] **APIs & Services** → **OAuth consent screen**
- [ ] User type: **External** (public) or **Internal** (Workspace only)
- [ ] Scopes: `openid`, `email`, `profile`
- [ ] Add **test users** while app is in Testing mode
- [ ] **Publish** the app when ready for public sign-in

### 4.3 Render env vars

```env
GOOGLE_CLIENT_ID=<from Google Console>
GOOGLE_CLIENT_SECRET=<from Google Console>
GOOGLE_REDIRECT_URI=FRONTEND_URL/auth/google/callback
```

- [ ] Add the three variables on Render
- [ ] Redeploy API

### 4.4 Verify Google sign-in

- [ ] Open `FRONTEND_URL/auth/sign-in` → click **Google**
- [ ] Complete login → land on `/app/dashboard`

| If you see… | Fix |
|-------------|-----|
| `redirect_uri_mismatch` | Redirect URI in Google Console must match `GOOGLE_REDIRECT_URI` exactly |
| `503 Google OAuth not configured` | Missing `GOOGLE_*` vars on Render; redeploy |
| CORS error in browser | `CORS_ALLOWED_ORIGINS` must include `FRONTEND_URL` (no trailing slash) |

---

## Phase 5 — GitHub OAuth

Detailed reference: [oauth-setup.md](oauth-setup.md#github-oauth)

### 5.1 GitHub OAuth App

- [ ] GitHub → **Settings** → **Developer settings** → **OAuth Apps** → **New OAuth App**
- [ ] **Application name:** CredenceAI (or your choice)
- [ ] **Homepage URL:** `FRONTEND_URL`
- [ ] **Authorization callback URL:** `FRONTEND_URL/auth/github/callback`
- [ ] Copy **Client ID**
- [ ] Generate **Client Secret**

For local dev, register `http://localhost:3000/auth/github/callback` as an additional callback (second OAuth app or update the same app).

### 5.2 Render env vars

```env
GITHUB_CLIENT_ID=<from GitHub>
GITHUB_CLIENT_SECRET=<from GitHub>
GITHUB_REDIRECT_URI=FRONTEND_URL/auth/github/callback
```

- [ ] Add the three variables on Render (Google vars can stay — both work together)
- [ ] Redeploy API

### 5.3 Verify GitHub sign-in

- [ ] Open `FRONTEND_URL/auth/sign-in` → click **GitHub**
- [ ] Authorize on GitHub → land on `/app/dashboard`

| If you see… | Fix |
|-------------|-----|
| Redirect URI not associated | Callback in GitHub app must match `GITHUB_REDIRECT_URI` |
| `incorrect_client_credentials` | Wrong client secret — regenerate in GitHub |
| Missing email / sign-in fails | Grant email access on GitHub; ensure primary email is set |

---

## Phase 6 — API keys (programmatic access)

After OAuth works:

- [ ] Sign in (Google or GitHub)
- [ ] Go to **Settings** → **Create API Key**
- [ ] Copy `cred_sk_...` immediately (shown only once)
- [ ] Store it in a password manager or secrets vault

### Validate with curl

```bash
# Health (no auth)
curl FRONTEND_URL/api/health
# Use API_URL for API calls:
curl API_URL/api/health

# Validate key
curl API_URL/api/auth/validate \
  -H "X-API-Key: cred_sk_YOUR_KEY"

# Submit a job
curl -X POST API_URL/api/jobs \
  -H "X-API-Key: cred_sk_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"job_type":"search_query","query":"test","input":"test"}'

# Revoke key in UI, retry job call → expect 401
```

- [ ] Health check returns 200
- [ ] API key validate returns `{"valid": true, ...}`
- [ ] Job submit returns `202`
- [ ] Revoked key returns `401`

---

## Phase 7 — GitHub Actions secrets (optional automation)

Repo → **Settings** → **Secrets and variables** → **Actions**

| Secret | Required? | Purpose |
|--------|-----------|---------|
| `RENDER_DEPLOY_HOOK_URL` | Optional | Auto-deploy API on push to `main` (from Render → service → Deploy Hook) |
| `API_URL` | Optional | Smoke tests + monitoring workflow |
| `DATABASE_URL` | Optional | Weekly backup workflow |
| `SMOKE_TEST_API_KEY` | Optional | Post-deploy API key test in CI |

- [ ] Add `RENDER_DEPLOY_HOOK_URL` if you want deploy-on-push
- [ ] Add `API_URL` for [monitor.yml](../.github/workflows/monitor.yml) health checks
- [ ] Add `DATABASE_URL` for [backup.yml](../.github/workflows/backup.yml) weekly dumps
- [ ] Add `SMOKE_TEST_API_KEY` after creating a test key in the UI

Vercel deploys automatically via Git integration — no GitHub secret needed for the frontend.

---

## Phase 8 — Monitoring and backups (optional)

### UptimeRobot (free external monitoring)

- [ ] Sign up at [uptimerobot.com](https://uptimerobot.com)
- [ ] Add HTTP monitor: `API_URL/api/health`
- [ ] Set alert email

### Render health check

- [ ] Confirm Render web service health check path is `/api/health`

### Database backups

- [ ] Enable weekly backups: ensure `DATABASE_URL` is set as a GitHub Actions secret (see Phase 7)
- [ ] Or schedule [`backend/scripts/backup_postgres.sh`](../backend/scripts/backup_postgres.sh) on a VPS (see [`backup_cron.example`](../backend/scripts/backup_cron.example))

---

## Phase 9 — Custom domain (when you have one)

Skip until you own a domain.

- [ ] DNS: `app.yourdomain.com` → Vercel, `api.yourdomain.com` → Render
- [ ] Update **Google** authorized origins and redirect URIs
- [ ] Update **GitHub** homepage and callback URL
- [ ] Update on Render: `GOOGLE_REDIRECT_URI`, `GITHUB_REDIRECT_URI`, `CORS_ALLOWED_ORIGINS`
- [ ] Update on Vercel: `VITE_API_BASE_URL=https://api.yourdomain.com/api`
- [ ] Redeploy frontend and API

---

## Quick reference — all env vars in one place

### Render (`credenceai-api` + worker)

```env
APP_ENV=production
MOCK_SERVICES=false
CELERY_ALWAYS_EAGER=false
RATE_LIMIT_ENABLED=true
ENABLE_API_KEY_AUTH=true
DATABASE_URL=<neon>
REDIS_URL=<upstash>
JWT_SECRET=<openssl rand -hex 32>
CORS_ALLOWED_ORIGINS=["https://your-app.vercel.app"]

GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://your-app.vercel.app/auth/google/callback

GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GITHUB_REDIRECT_URI=https://your-app.vercel.app/auth/github/callback
```

### Vercel

```env
VITE_API_BASE_URL=https://your-api.onrender.com/api
```

---

## Known limitations (free tier)

- Search runs in **degraded mode** without OpenSearch, MinIO, and SearXNG (SQLite + ephemeral storage on Render).
- Render free tier services **spin down** after inactivity; first request may be slow.
- Neon free tier has storage/connection limits; upgrade when you outgrow them.

For a full search stack, use Docker Compose on a VPS — see [deployment.md](deployment.md#docker-compose-full-stack).

---

## Related docs

| Doc | Contents |
|-----|----------|
| [deployment.md](deployment.md) | Architecture, Compose deploy, CI/CD overview |
| [oauth-setup.md](oauth-setup.md) | OAuth troubleshooting detail |
| [environment.md](environment.md) | Full variable reference |
| [backend/.env.production.example](../backend/.env.production.example) | Production env template |
