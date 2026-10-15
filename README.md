# CredenceAI

**Search intelligence for researchers, analysts, and builders.**

CredenceAI turns natural-language questions into multi-source evidence: it classifies intent, orchestrates retrieval (SearXNG, Wikidata, Wikipedia, GDELT, OpenAlex, Common Crawl), normalizes and scores results, and exposes them through a FastAPI backend, React app, and TypeScript SDK.

[![CI](https://github.com/Niruuu2005/CredenceAI/actions/workflows/ci.yml/badge.svg)](https://github.com/Niruuu2005/CredenceAI/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](backend/requirements.txt)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue.svg)](sdk/package.json)

---

## Quick start

**Developer mode** (recommended):

```powershell
.\scripts\dev.ps1
```

Or manually:

```bash
git clone https://github.com/Niruuu2005/CredenceAI.git
cd CredenceAI
```

### Backend

```bash
cd backend
cp .env.development .env    # or .env.example on older setups
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
set PYTHONPATH=src
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend

```bash
cd frontend
cp .env.development .env
npm install
npm run dev
```

Open http://localhost:3000 → sign in → run a search from the app.

**Production mode:** Frontend on Vercel proxies `/api` to Render. See [docs/architecture.md](docs/architecture.md#21-production-deployment-runbook-vercel--render) and run `.\scripts\prod-check.ps1` before deploy.

### Tests

```bash
cd backend && pytest -q
cd ../sdk && npm ci && npm test
cd ../frontend && npm run lint && npm run build
```

---

## Repository layout

```
/
├── backend/       FastAPI API, Celery workers, Alembic migrations
├── frontend/      React + Vite SPA (Vercel)
├── sdk/           @credenceai/sdk TypeScript client
├── agentgate/     NANDAHack Phase 2 microservice (separate Render deploy)
├── scripts/       dev.ps1, prod-check.ps1, e2e tests
├── docs/          Consolidated Documentation Suite (SRS, BRD, Architecture, Checklist, Master)
├── .github/       CI workflows
└── render.yaml    CredenceAI API Render blueprint
```

Full map: [docs/architecture.md#19-monorepo-structure--component-directory-map](docs/architecture.md#19-monorepo-structure--component-directory-map)

---

## Features

- **Intent classification** — routes queries to the right vertical and sources
- **Job pipeline** — async search jobs with normalized results and quality scores
- **Goal decomposition** — breaks complex research goals into executable sub-jobs
- **Evidence graph** — entity linking, claims, intelligence cards
- **Vertical packs** — company, research, news, RAG dataset workflows
- **Monitors & collections** — per-user workspace objects with plan quotas
- **Auth & billing** — Google OAuth, JWT sessions, Stripe Checkout
- **Multi-tenant security** — user-scoped jobs, monitors, collections, API keys

---

## Tech stack

| Layer | Stack |
|-------|--------|
| API | FastAPI, SQLAlchemy, Alembic, Celery, Redis |
| Search | SearXNG, OpenSearch/SQLite fallback, hybrid ranking |
| Frontend | React, Vite, Tailwind, TypeScript |
| SDK | TypeScript, Vitest |
| Deploy | Docker, nginx, GitHub Actions CI |

---

## Environment variables

See [docs/architecture.md#20-environment-variables-reference-catalog](docs/architecture.md#20-environment-variables-reference-catalog). Copy examples — never commit real secrets:

- `backend/.env.example`
- `frontend/.env.example`
- `sdk/.env.example`

Production requires `JWT_SECRET`, at least one OAuth provider (Google and/or GitHub), and Stripe keys for paid plans. See [docs/architecture.md#22-oauth-authentication-setup--troubleshooting](docs/architecture.md#22-oauth-authentication-setup--troubleshooting).

---

## Deployment

**Production (Vercel + Render):** follow the complete guide in **[docs/architecture.md#21-production-deployment-runbook-vercel--render](docs/architecture.md#21-production-deployment-runbook-vercel--render)**.

**Self-hosted (Docker Compose):**

```bash
cd backend
docker compose -f docker-compose.prod.yml up --build
```

---

## Documentation

The project documentation is cleanly consolidated into 5 comprehensive documents in the [`docs/`](docs/) directory:

| Document | Description |
|----------|-------------|
| **[CredenceAI 2.0 Master Guide](docs/CredenceAI%202.0.md)** | Core vision, 8-step pipeline explanation, UI/UX 3-palette theme system, changelog, and contributing guidelines. |
| **[System Architecture & Operations](docs/architecture.md)** | End-to-end architecture, repository layout, deployment runbooks (Vercel + Render), OAuth setup, 40–45s keep-alive loop, SDK spec, and day-2 operations. |
| **[Software Requirements Specification (SRS)](docs/srs.md)** | Formal system requirements, full REST API endpoints and schemas, and 12-table PostgreSQL database schema. |
| **[Business Requirements Document (BRD)](docs/brd.md)** | Strategic positioning, competitive differentiation matrix, rural and urban public impact domains, and commercial models. |
| **[100% Release Acceptance Checklist](docs/checklist.md)** | 12 Hard Go/No-Go release gates (G1–G12), production readiness scorecard, and audit verification records. |

---

## License

MIT — see [LICENSE](LICENSE).

---

## Contributing & Security

See [Contributing Guidelines](docs/CredenceAI%202.0.md#25-contributing-guidelines) and [Security Policy](docs/architecture.md#16-security-compliance-and-responsible-ai).
