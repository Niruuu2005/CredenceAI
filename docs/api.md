# API Reference

Base URL: `http://localhost:8000` (development). Most frontend calls use the `/api` prefix.

## Authentication

| Method | Requirement |
|--------|-------------|
| JWT Bearer | `Authorization: Bearer <token>` — session auth from Google OAuth or dev login |
| API key | `X-API-Key: cred_sk_...` when `ENABLE_API_KEY_AUTH=true` |

## Health

### `GET /api/health`

Returns service status, version, and dependency checks.

**Auth:** None

## Jobs

### `POST /api/jobs`

Submit a search job.

**Auth:** JWT Bearer (required)

**Body:**
```json
{
  "job_type": "search_query",
  "input": "quantum computing trends",
  "query": "quantum computing trends",
  "priority": "normal",
  "mode": "standard"
}
```

**Response:** `202` — `{ "job_id", "trace_id", "status", "created_at" }`

### `GET /api/jobs`

List jobs for the authenticated user. Query params: `limit`, `offset`, `status`, `q`.

**Auth:** JWT Bearer (required)

### `GET /api/jobs/{job_id}`

Job status and result summary.

**Auth:** JWT Bearer (required)

## Search

### `GET /api/search?q={query}&limit={n}`

Hybrid search over indexed documents.

**Auth:** JWT Bearer (required)

## Goals

### `POST /api/goals`

**Auth:** JWT Bearer (required)

**Body:** `{ "goal": "...", "vertical": "general" }`

Decomposes a goal into planner jobs.

## Auth

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/auth/google/url` | GET | None | Google OAuth URL (mock in local dev) |
| `/api/auth/google/callback` | POST | None | Exchange OAuth code for JWT |
| `/api/auth/login` | POST | None | Dev credentials login (`APP_ENV=local` only) |
| `/api/auth/me` | GET | JWT | Current user profile |
| `/api/auth/me` | PATCH | JWT | Update profile (name) |
| `/api/auth/upgrade` | POST | JWT | Local-only mock upgrade; **410 in production** |
| `/api/auth/keys` | GET/POST | JWT | List/create API keys (scoped to user) |
| `/api/auth/keys/{id}` | DELETE | JWT | Revoke API key |

## Billing

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/billing/checkout-session` | POST | JWT | Create Stripe Checkout session |
| `/api/billing/portal-session` | POST | JWT | Stripe Customer Portal |
| `/api/billing/status` | GET | JWT | Plan, usage, subscription status |
| `/api/billing/webhook` | POST | Stripe signature | Stripe webhook (no JWT) |

## Monitors

**Auth:** JWT Bearer (required) — all routes scoped to owner.

| Endpoint | Method |
|----------|--------|
| `/api/monitors` | GET, POST |
| `/api/monitors/{id}` | DELETE |
| `/api/monitors/{id}/sync` | POST |

## Collections

**Auth:** JWT Bearer (required) — all routes scoped to owner.

| Endpoint | Method |
|----------|--------|
| `/api/collections` | GET, POST |
| `/api/collections/{id}` | DELETE |

## Agents, evidence, intelligence, verticals

See OpenAPI docs at `/docs` when the backend is running.

## Backward compatibility

Routes are also mounted without `/api` prefix for SDK and legacy clients.

## Error format

```json
{
  "error": "validation_error",
  "message": "Human-readable message",
  "trace_id": "trace_abc123",
  "details": []
}
```

Common status codes: `400`, `401`, `403`, `422`, `429`, `500`, `503`.
