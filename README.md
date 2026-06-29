# CredenceAI

**Search intelligence for researchers, analysts, and builders.**

CredenceAI turns natural-language questions into multi-source evidence: it classifies intent, orchestrates retrieval (SearXNG, Wikidata, Wikipedia, GDELT, OpenAlex, Common Crawl), normalizes and scores results, and exposes them through a FastAPI backend, React app, and TypeScript SDK.

[![CI](https://github.com/Niruuu2005/CredenceAI/actions/workflows/ci.yml/badge.svg)](https://github.com/Niruuu2005/CredenceAI/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE.md)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](backend/requirements.txt)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue.svg)](sdk/package.json)

---

## Quick start

**Prerequisites:** Python 3.11+, Node 20+, Git

```bash
git clone https://github.com/Niruuu2005/CredenceAI.git
cd CredenceAI
```

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
cp .env.example .env            # or copy on Windows
set PYTHONPATH=src                # export PYTHONPATH=src on Unix
set APP_ENV=local
set CELERY_ALWAYS_EAGER=true
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- API docs: http://localhost:8000/docs  
- Health: http://localhost:8000/api/health  

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:3000 → sign in → run a search from the app.

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
├── backend/     FastAPI API, Celery workers, Alembic migrations
├── frontend/    React + Vite SPA
├── sdk/         @credenceai/sdk TypeScript client
├── docs/        Architecture, API, deployment, operations
├── .github/     CI workflows
└── README.md
```

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

See [docs/environment.md](docs/environment.md). Copy examples — never commit real secrets:

- `backend/.env.example`
- `frontend/.env.example`
- `sdk/.env.example`

Production requires `JWT_SECRET`, Google OAuth (`GOOGLE_*`), and Stripe keys for paid plans.

---

## Deployment

```bash
cd backend
docker compose -f docker-compose.prod.yml up --build
```

Details: [docs/deployment.md](docs/deployment.md)

---

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/architecture.md](docs/architecture.md) | System design |
| [docs/api.md](docs/api.md) | REST API reference |
| [docs/deployment.md](docs/deployment.md) | Production deployment |
| [docs/database.md](docs/database.md) | Schema and migrations |
| [docs/testing.md](docs/testing.md) | Test commands |

---

## License

MIT — see [LICENSE.md](LICENSE.md).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security policy: [SECURITY.md](SECURITY.md).
