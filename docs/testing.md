# Testing

## Backend (pytest)

```bash
cd backend
python -m pytest
```

**Verified:** 250 tests passing (in-memory SQLite, mocked SearXNG in `conftest.py`).

Configuration: `backend/pytest.ini` (`pythonpath = src`, `testpaths = tests`)

Tests use in-memory SQLite and mock SearXNG responses via `conftest.py`.

### Auth production guards

`tests/test_auth_production_guards.py` verifies mock OAuth and dev login are disabled when `APP_ENV=production`.

## SDK (vitest)

```bash
cd sdk
npm install
npm test
```

**Verified:** 20 tests passing.

## Frontend

```bash
cd frontend
npm run lint     # TypeScript check
npm run build    # production build verification
```

## E2E scripts

```bash
cd backend
set CREDENCEAI_BASE_URL=http://localhost:8000
set PYTHONPATH=src
python scripts/check_realtime.py
python scripts/browser_e2e_tests.py
```

Requires a running backend instance.

## CI recommendation

1. `cd backend && pip install -r requirements.txt && python -m pytest`
2. `cd sdk && npm ci && npm run build && npm test`
3. `cd frontend && npm ci && npm run lint && npm run build`
