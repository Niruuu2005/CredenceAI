# SDK

TypeScript/JavaScript client published as [`@credenceai/sdk`](https://www.npmjs.com/package/@credenceai/sdk).

Source of truth in this monorepo: `sdk/`.

## Install (monorepo)

```bash
cd sdk
npm ci
npm run build
```

Frontend depends on it via `"@credenceai/sdk": "file:../sdk"` in `frontend/package.json`.

## Usage

```typescript
import { CredenceAIClient } from "@credenceai/sdk";

const client = new CredenceAIClient({
  apiKey: "cred_sk_...",
  baseUrl: "http://localhost:8000",
});

const health = await client.health();
const job = await client.createJob({ query: "AI regulation 2026" });
const result = await client.run("AI regulation 2026");
```

### Browser session auth

```typescript
const client = new CredenceAIClient({
  baseUrl: "http://localhost:8000",
  apiPrefix: "/api",
  getAccessToken: () => localStorage.getItem("cred_token"),
});

const user = await client.auth.getCurrentUser();
const monitors = await client.monitors.list();
```

The HTTP client binds `fetch` to `globalThis` so browser calls do not throw `Illegal invocation`.

## Environment (`fromEnv`)

```bash
CREDENCEAI_BASE_URL=http://localhost:8000
CREDENCEAI_API_KEY=cred_sk_...
```

```typescript
const client = CredenceAIClient.fromEnv();
```

## Services

| Service | Methods |
|---------|---------|
| Jobs | `createJob`, `getJob`, `listJobs`, `run` |
| Search | `search` |
| Health | `health` |
| Auth | `getGoogleAuthUrl`, `loginWithGoogle`, `loginWithCredentials`, `getCurrentUser`, `upgradePlan`, API keys |
| Monitors | `list`, `create`, `sync`, `delete` |
| Collections | `list`, `create`, `delete` |
| Goals | `submit` |

## Build and test

```bash
npm run build    # tsup → dist/
npm test         # vitest
npm run lint
```

## Publishing

1. Bump version in `sdk/package.json`.
2. `npm run build && npm test`
3. `npm publish --access public` from `sdk/`

Document API changes in root `CHANGELOG.md`.
