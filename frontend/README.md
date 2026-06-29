# CredenceAI Frontend

React SPA for CredenceAI marketing pages and authenticated app.

## Setup

```bash
npm ci
cp .env.example .env
npm run dev
```

Open http://localhost:3000

## Environment

| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | Backend API URL including `/api`, e.g. `http://localhost:8000/api` |

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Vite dev server with `/api` proxy |
| `npm run build` | Production build to `dist/` |
| `npm run lint` | TypeScript check |
| `npm run preview` | Preview production build |

API calls use `@credenceai/sdk` via `src/lib/api.ts`.
