# Repository layout

CredenceAI is a **monorepo**. Each top-level folder is an independent deployable or publishable package.

```
CredenceAI/
├── backend/              # FastAPI API, Celery workers, Alembic migrations
│   ├── src/app/          # Application code (api, agents, services, verticals)
│   ├── migrations/       # Database migrations (alembic)
│   ├── tests/            # pytest suite
│   ├── Dockerfile        # Production image (Render / self-hosted)
│   └── docker-compose.yml
│
├── frontend/             # React + Vite SPA (Vercel)
│   ├── src/pages/        # marketing, auth, app workspace
│   └── nginx.conf        # Docker / self-hosted API proxy
│
├── sdk/                  # @credenceai/sdk TypeScript HTTP client
│
├── agentgate/            # NANDAHack Phase 2 — separate microservice (Render)
│   ├── main.py           # FastAPI app
│   ├── SKILL.md          # Agent-readable skill doc
│   └── render.yaml       # Optional Render blueprint
│
├── scripts/              # Developer and ops helpers
│   ├── dev.ps1           # Start backend + frontend locally
│   ├── prod-check.ps1    # Validate production env before deploy
│   └── e2e/              # End-to-end test scripts
│
├── Submission/           # Hackathon deliverables (SKILL.md, demo scripts)
│
├── docs/                 # Architecture, API, deployment guides
│   └── archive/specs/    # Historical design specs
│
├── .github/workflows/    # CI (backend, frontend, sdk)
├── render.yaml           # CredenceAI API Render blueprint
├── IMPROVEMENTS.md       # Platform gap tracker (agentic roadmap)
└── README.md             # Start here
```

## What runs where

| Package | Production host | URL |
|---------|-----------------|-----|
| CredenceAI API | Render (`credenceai-api`) | https://credenceai-api.onrender.com |
| CredenceAI UI | Vercel | https://credence-ai-gamma.vercel.app |
| AgentGate | Render (`agentgate`) | https://agentgate-xwqo.onrender.com |

**CredenceAI** and **AgentGate** are separate services. Do not merge their deploy configs.

## Branches

| Branch | Purpose |
|--------|---------|
| `master` | Main CredenceAI platform (production) |
| `hackathon/agentgate` | AgentGate hackathon submission (can merge agentgate/ folder to master) |

## Quick commands

```powershell
.\scripts\dev.ps1              # Local dev
.\scripts\prod-check.ps1       # Pre-deploy validation
cd backend && pytest -q        # Backend tests
cd frontend && npm run build   # Frontend build
```

See [README.md](../README.md) and [environment.md](environment.md) for full setup.
