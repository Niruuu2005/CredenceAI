# Environment Variables

## Mode Profiles

CredenceAI supports two primary runtime modes:

| Profile | `APP_ENV` | Backend | Frontend API |
|---------|-----------|---------|--------------|
| **Developer** | `development` or `local` | `localhost:8000` | Vite proxy `/api` → backend |
| **Production** | `production` | Render or Docker | Vercel `/api` rewrite → Render |

**Quick start (developer mode):**
```powershell
.\scripts\dev.ps1
```

**Pre-deploy validation:**
```powershell
.\scripts\prod-check.ps1
```

Env templates: `backend/.env.development`, `backend/.env.production`, `frontend/.env.development`, `frontend/.env.production`

---

## Backend (`backend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_ENV` | No | `local` | `development`, `local`, or `production` |
| `DATABASE_URL` | Yes | postgres URL | SQLAlchemy DSN |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Celery broker |
| `MOCK_SERVICES` | No | `false` | Use fallbacks when services down |
| `CELERY_ALWAYS_EAGER` | No | `true` | Inline task execution |
| `OPENAI_API_KEY` | For LLM features | — | OpenAI API key |
| `OPENSEARCH_URL` | No | `http://localhost:9200` | Search index |
| `MINIO_ENDPOINT` | No | `http://localhost:9000` | Object storage |
| `SEARXNG_BASE_URL` | No | `http://localhost:8080` | Meta-search |
| `ENABLE_API_KEY_AUTH` | Prod | `false` | Require `X-API-Key` on protected routes |
| `ENABLE_API_DOCS` | No | `true` | Serve `/docs`, `/redoc`, `/openapi.json` (public API UI) |
| `CORS_ALLOWED_ORIGINS` | Prod | localhost:3000 | JSON array of origins |
| `JWT_SECRET` | Prod | change-me | JWT signing secret |
| `DB_POOL_SIZE` | No | `5` | PostgreSQL connection pool size |
| `DB_MAX_OVERFLOW` | No | `10` | Pool overflow connections |
| `DB_POOL_RECYCLE` | No | `1800` | Recycle connections after seconds |
| `STRIPE_SECRET_KEY` | Billing | — | Stripe API secret |
| `STRIPE_WEBHOOK_SECRET` | Billing | — | Stripe webhook signing secret |
| `STRIPE_PRICE_ID_PRO` | Billing | — | Stripe price ID for Pro plan |
| `STRIPE_PRICE_ID_ENTERPRISE` | Billing | — | Stripe price ID for Enterprise |
| `STRIPE_SUCCESS_URL` | Billing | — | Checkout success redirect URL |
| `STRIPE_CANCEL_URL` | Billing | — | Checkout cancel redirect URL |
| `GOOGLE_CLIENT_ID` | OAuth | — | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | OAuth | — | Google OAuth secret |
| `GOOGLE_REDIRECT_URI` | OAuth | — | Frontend callback URL (`/auth/google/callback`) |
| `GITHUB_CLIENT_ID` | OAuth | — | GitHub OAuth client ID |
| `GITHUB_CLIENT_SECRET` | OAuth | — | GitHub OAuth secret |
| `GITHUB_REDIRECT_URI` | OAuth | — | Frontend callback URL (`/auth/github/callback`) |
| `DEV_LOGIN_USERNAME` | Local dev | — | Developer login user |
| `DEV_LOGIN_PASSWORD` | Local dev | — | Developer login password |
| `RATE_LIMIT_ENABLED` | No | `false` | Enable rate limiting |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `ENABLE_AGENTIC_PIPELINE` | No | `true` | Enable multi-agent orchestration |
| `AGENT_MAX_ITERATIONS` | No | `3` | Max replanning iterations per job |
| `MAX_GOAL_JOBS_EAGER` | No | `1` | Max goal jobs when Celery eager |
| `MAX_GOAL_JOBS_WORKER` | No | `10` | Max goal jobs with dedicated worker |
| `SEARCH_PROVIDER` | No | `auto` | `auto` / `searxng` / `duckduckgo` |
| `ENABLE_WIKIPEDIA` / `ENABLE_WIKIDATA` | No | `true` | Wiki search adapters |
| `ENABLE_GDELT` / `ENABLE_OPENALEX` / `ENABLE_CROSSREF` / `ENABLE_ARXIV` | No | `true` | News + scholarly adapters |
| `ENABLE_COMMONCRAWL` | No | `true` | Crawl fallback to Common Crawl |
| `SCHOLARLY_MAILTO` | No | `contact@credenceai.org` | Polite pool contact for OpenAlex/Crossref |

**Production:** at least one OAuth provider (Google or GitHub) plus strong `JWT_SECRET`. See [`backend/.env.production.example`](../backend/.env.production.example) and [oauth-setup.md](oauth-setup.md).

Source selection only uses executable free adapters; paid SERP/NewsAPI/Crunchbase are not selected. See `backend/.env.example` for full adapter and budget settings.

## Frontend (`frontend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_BASE_URL` | Yes | API URL with `/api`, e.g. `http://localhost:8000/api` |

## SDK (`sdk/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `CREDENCEAI_BASE_URL` | Yes | API host, e.g. `http://localhost:8000` |
| `CREDENCEAI_API_KEY` | For `fromEnv()` | API key `cred_sk_...` |

## Scripts

| Variable | Default | Description |
|----------|---------|-------------|
| `CREDENCEAI_BASE_URL` | `http://localhost:8000` | Target for E2E scripts |

## GitHub Actions secrets

| Secret | Purpose |
|--------|---------|
| `RENDER_DEPLOY_HOOK_URL` | Trigger Render deploy |
| `API_URL` | Smoke tests and monitoring |
| `DATABASE_URL` | Weekly backup workflow |
| `SMOKE_TEST_API_KEY` | Optional API key smoke test |
