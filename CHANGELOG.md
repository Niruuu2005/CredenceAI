# Changelog

## [Unreleased] — Production readiness

### Security & multi-tenant

- Mock auth bypass (`mock_jane_doe`) restricted to `APP_ENV=local` only.
- Jobs, monitors, collections, search, goals, and API keys require authentication.
- Per-user scoping on jobs, monitors, and collections with isolation tests.
- Daily quota semantics via `usage_period_start`; per-user monitor/collection limits.

### Database

- Alembic migration `b1c2d3e4f5a6` for users, billing fields, monitors/collections `user_id`, indexes.
- Production startup uses Alembic only; `create_all()` limited to local/test.
- Docker entrypoint runs `alembic upgrade head` before uvicorn.

### User management & billing

- User model extended with Stripe subscription fields, `role`, `account_status`.
- Admin endpoints: list users, suspend account.
- Stripe Checkout, Customer Portal, webhook handler with idempotency.
- `POST /auth/upgrade` disabled in production; frontend uses Stripe checkout.

### Ops & CI

- GitHub Actions CI for backend, SDK, and frontend.
- Production config validation (JWT, Google OAuth).
- Redis health check, rate limits in prod compose, nginx security headers.

### Added tests

- `test_user_isolation.py`, `test_api_keys_auth_required.py`, `test_billing.py`.

---

## [Unreleased] — Monorepo restructure

### Changed

- Restructured repository into `backend/`, `frontend/`, `sdk/`, and `docs/`.
- Backend is API-only; React SPA runs as a separate frontend service.
- Vendored `@credenceai/sdk` into `sdk/` with auth, monitors, collections, and goals support.
- Frontend uses SDK via `file:../sdk` dependency instead of duplicated `api.ts` HTTP logic.
- Developer login and Google mock auth gated to `APP_ENV=local` with env-based credentials.
- CORS configured for split frontend deployment.

### Added

- Operational documentation under `docs/`.
- `backend/pytest.ini`, `frontend/Dockerfile`, `sdk/.env.example`.
- Production auth guard tests in `backend/tests/test_auth_production_guards.py`.

### Fixed

- SDK browser `fetch` binding (`Illegal invocation` in frontend sign-in).

### Removed

- Legacy root `src/` tree, `run_app.ps1`, `run_app.bat`, and root `ARCHITECTURE.md`.
- Embedded frontend from `backend/src/app/templates/` (moved to `frontend/`).
- Flat `docs/docs/*` specs (archived to `docs/archive/specs/`).

---

## Refined Documentation Package

### Added

- Clear CredenceAI definition and USP.
- Strict researcher evaluation of the project.
- Broader use-case strategy using vertical intelligence packs.
- Detailed community impact table.
- Five-iteration scope and expectation plan.
- Per-iteration architecture end-states from Iteration 0.1 through Iteration 0.5.
- Accuracy, efficiency, and response-time tuning strategy.
- Evidence graph and claim-level provenance model.
- Fast, Standard, and Deep execution modes.
- RAG-ready output contracts.
- Expanded testing, benchmarking, A/B testing, and acceptance criteria.

### Refined

- Reframed project from a general search tool to a trusted intelligence layer.
- Narrowed MVP scope to reduce overbuilding risk.
- Split batch/deep research workflows from interactive search workflows.
- Added stronger controls around AI agents so they assist but do not bypass deterministic policy gates.

### Preserved

- Original free-first, open-source operating model.
- Source orchestration concept.
- Quality scoring, deduplication, entity resolution, safe crawling, extraction, indexing, observability, and benchmarking principles.
