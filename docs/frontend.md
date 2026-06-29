# Frontend

React 19 SPA built with Vite and Tailwind CSS.

## Setup

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Dev server: http://localhost:3000

## Environment

| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | Backend API base including `/api` suffix, e.g. `http://localhost:8000/api` |

In development, Vite proxies `/api` to the backend host derived from `VITE_API_BASE_URL`.

## API client

All HTTP calls go through `src/lib/api.ts`, which wraps `@credenceai/sdk` (`file:../sdk`).

## Local development with frontend

1. Start backend (port 8000 or 8012).
2. Copy `frontend/.env.example` → `frontend/.env`.
3. Set `VITE_API_BASE_URL` to match your backend, e.g. `http://localhost:8000/api`.
4. Run `npm run dev` in `frontend/`.

The frontend uses `@credenceai/sdk` through `src/lib/api.ts` with Bearer token session auth. In local mode (`APP_ENV=local`), mock Google auth is available when OAuth env vars are unset.

## Build

```bash
npm run build    # output: dist/
npm run preview  # preview production build
```

## Docker

Built from repo root context:

```bash
docker build -f frontend/Dockerfile --build-arg VITE_API_BASE_URL=https://api.example.com/api -t credenceai-frontend .
```

Served via nginx on port 80 with SPA fallback routing.

## Structure

| Path | Purpose |
|------|---------|
| `src/pages/app/` | Authenticated app screens |
| `src/pages/auth/` | Sign-in, sign-up, OAuth callback |
| `src/pages/marketing/` | Public marketing pages |
| `src/layouts/` | App, auth, marketing layouts |
| `src/lib/api.ts` | SDK wrapper + session helpers |
