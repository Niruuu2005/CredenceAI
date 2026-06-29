# Contributing to CredenceAI

Thank you for contributing. This monorepo contains `backend/`, `frontend/`, `sdk/`, and `docs/`.

## Development setup

1. Clone the repository.
2. Follow [README.md](README.md) to run backend and frontend locally.
3. Copy each package's `.env.example` to `.env` — never commit secrets.

## Branch workflow

1. Create a feature branch from `main`.
2. Make focused changes in the appropriate package directory.
3. Run tests for affected packages before opening a PR.
4. Update operational docs in `docs/` when behavior or env vars change.

## Code conventions

- **Backend:** Python 3.11, FastAPI, SQLAlchemy. Keep route handlers thin; business logic in `src/app/services/`.
- **Frontend:** React 19, Vite, TypeScript. Use `@credenceai/sdk` via `src/lib/api.ts` — do not duplicate HTTP calls.
- **SDK:** TypeScript, tsup build. Extend services in `sdk/src/services/` and export types from `sdk/src/types/`.

## Running checks

```bash
cd backend && python -m pytest
cd sdk && npm run build && npm test
cd frontend && npm run lint && npm run build
```

## Security

Do not commit credentials. Report vulnerabilities per [SECURITY.md](SECURITY.md).
