# CredenceAI — Improvements Tracker

Living document tracking the gap between current state and a complete, public-ready agentic AI platform.
Cross-reference: [UI_UX_FIXES.md](UI_UX_FIXES.md) for detailed frontend UX notes.

**Last updated:** 2026-07-09

---

## 1. Executive Summary

CredenceAI is an **AI-assisted search intelligence platform** with strong retrieval, scoring, and citation infrastructure. It does **not yet qualify** as a complete agentic AI system: runtime behavior is mostly a fixed deterministic pipeline with optional one-shot LLM planning.

**Target:** Full agentic architecture per [docs/archive/specs/20_AGENTIC_AI_LAYER.md](docs/archive/specs/20_AGENTIC_AI_LAYER.md).

**Primary persona:** Compliance analysts, researchers, and due-diligence teams who need cited, multi-source evidence on entities, news, and scholarly topics.

---

## 2. Agentic AI Checklist

| Criterion | Status | Notes |
|-----------|--------|-------|
| Autonomous multi-step loop with replanning | In progress | `AgentOrchestrator` added with iteration cap |
| LLM tool calling / function routing | In progress | `llm_client.py` tool schema support |
| Multi-agent orchestration at runtime | In progress | 5 agents wired via orchestrator |
| Planning drives execution | In progress | Goals multi-job when worker available |
| Agent memory across turns | In progress | `AgentWorkingMemory` per job |
| Agent budget enforcement | Done | Budget controller integrated in `BaseAgent.execute` |
| CrawlStrategyAgent | Done | `crawl_strategy_agent.py` |
| ExperimentAgent | Done | `experiment_agent.py` |
| OpsRecoveryAgent | Done | `ops_recovery_agent.py` |

---

## 3. Dev / Production Mode Matrix

| Setting | Developer (`APP_ENV=development`) | Production (`APP_ENV=production`) |
|---------|-----------------------------------|-----------------------------------|
| Backend URL | `http://localhost:8000` | `https://credenceai-api.onrender.com` |
| Frontend URL | `http://localhost:3000` | `https://credence-ai-gamma.vercel.app` |
| API routing | Vite proxy `/api` → backend | Vercel rewrite `/api` → Render |
| Database | SQLite or local Postgres | Neon PostgreSQL |
| `MOCK_SERVICES` | `true` (optional) | `false` (required) |
| OAuth | Mock codes allowed | Google/GitHub only |
| Celery | `CELERY_ALWAYS_EAGER=true` | Eager on free tier; worker on paid |
| Search | SearXNG (Docker) or DuckDuckGo | DuckDuckGo |
| Auth | Dev login + mock OAuth | OAuth + API keys |

**Quick start:**
```powershell
.\scripts\dev.ps1          # Start backend + frontend in dev mode
.\scripts\prod-check.ps1   # Validate production env before deploy
```

Env templates: `backend/.env.development`, `backend/.env.production`, `frontend/.env.development`, `frontend/.env.production`

---

## 4. Half-Baked Features

### P0 — Blocks public use

| Feature | Issue | Fix | Status |
|---------|-------|-----|--------|
| Monitors | `sync` was a no-op | Celery beat + real search job enqueue | Done |
| Goal research | Capped to 1 job on eager | Dynamic cap based on worker mode | Done |
| Agent layer | 4/5 agents unwired | Wired in orchestrator + agent orchestrator | Done |
| Settings prefs | localStorage only | `UserPreferences` API + frontend sync | Done |
| Collections | No result linking | `CollectionItem` model + API + UI | Done |
| Billing | Silent prod failure | Clear error messages + Stripe validation | Done |
| Docs page | Placeholder links | Real links to docs/ and API reference | Done |
| Enterprise form | UI only | Backend contact endpoint | Done |

### P1 — Quality / trust

| Feature | Issue | Fix | Status |
|---------|-------|-----|--------|
| Evidence graph | No frontend | Evidence panel in SearchApp | Done |
| Agent trail | Not visible | Agent decisions panel in SearchApp | Done |
| RAG vertical | Mock embeddings | Disabled until real provider | Done |
| Source diversity | DDG only in prod | SourceSelectionAgent picks adapters | Done |
| UI light mode | Invisible card text | `text-text-title` on CardTitle | Done |

### P2 — Polish

| Feature | Issue | Fix | Status |
|---------|-------|-----|--------|
| Mobile sidebar | Fixed width | Responsive drawer | Pending |
| Native confirm() | Breaks UX | Radix dialogs | Partial |
| Synthesis prominence | On-demand only | Shown in search results flow | Done |

---

## 5. Public Launch Blockers

| Blocker | Resolution | Status |
|---------|------------|--------|
| Mock OAuth in prod | Gated to `APP_ENV=development` | Done |
| `MOCK_SERVICES` in prod | Startup validation rejects | Done |
| No Celery worker | `render.yaml` worker service option documented | Done |
| Stripe not configured | Startup warning + clear UI message | Done |
| Legacy `/dashboard` | Removed from prod routes | Done |

---

## 6. UI/UX Backlog

Distilled from [UI_UX_FIXES.md](UI_UX_FIXES.md):

- [x] P0: Fix `CardTitle` invisible text in light mode
- [ ] P1: Responsive sidebar drawer on mobile
- [ ] P1: Replace native `confirm()` with Radix dialogs (Settings done, Collections/Monitors partial)
- [ ] P2: Unify light/dark theme accent colors
- [ ] P2: Minimum font size 11px for labels

---

## 7. Cleanup Log

| Item | Action | Date |
|------|--------|------|
| Legacy `/dashboard` HTML route | Removed from `main.py` | 2026-07-09 |
| `browser_e2e_tests.py` | Moved to `scripts/e2e/` | 2026-07-09 |
| Company vertical mock contradiction | Removed | 2026-07-09 |
| RAG mock embeddings | Vertical disabled with clear message | 2026-07-09 |
| Mock OAuth | Gated to development only | 2026-07-09 |
| `mock_jane_doe` auto-provision | Development only | 2026-07-09 |

---

## 8. Phase Tracker

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | IMPROVEMENTS.md audit doc | Done |
| 1 | Dev/prod mode profiles + scripts | Done |
| 2 | Wire existing agents into orchestrator | Done |
| 3 | Agent loop + tool calling + new agents | Done |
| 4 | Real monitors + goals multi-job | Done |
| 5 | Frontend completion (settings, collections, evidence) | Done |
| 6 | Cleanup mock/demo + restructure | Done |
| 7 | Production hardening (Render worker, Stripe, nginx) | Done |

---

## 9. Completed

- [x] IMPROVEMENTS.md created
- [x] Dev/prod env templates and scripts
- [x] Agent budget controller wired into BaseAgent
- [x] SourceSelection, QualityCritic, EntityResolution, ExtractionValidation agents in pipeline
- [x] AgentOrchestrator with replanning loop
- [x] CrawlStrategy, Experiment, OpsRecovery agents
- [x] Monitor sync via search job enqueue
- [x] User preferences API
- [x] Collection items API
- [x] Enterprise contact form backend
- [x] Evidence graph + agent trail in SearchApp
- [x] Production startup validation for agentic + mock guards
- [x] Render worker blueprint option
- [x] Docker nginx API proxy
