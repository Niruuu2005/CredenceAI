# CredenceAI SDK Implementation Guide

## Purpose

This document defines the recommended implementation plan for the **CredenceAI JavaScript/TypeScript SDK**. It is based on the current backend shape described in the project documentation and adapted to the clarified product decisions:

- SDK target: **JavaScript / TypeScript**
- Distribution: **open-source**
- Auth model: **API key issued by your own backend**
- API key format: `cred_sk_...`
- Authentication method: **header-based**, using `X-API-Key`
- API coverage: wrap **all four public endpoints**
- Consumer experience: provide a **single blocking-style abstraction** for primary usage, while still exposing lower-level methods for control

The goal is to make it easy for any external project to install the SDK, provide an API key at initialization time, call CredenceAI services safely, and receive typed, predictable responses.

---

## Backend Understanding

The available project files show that CredenceAI is a modular search-intelligence system built around a **FastAPI REST API**, a **job-based orchestration flow**, async task execution with **Celery**, storage/index adapters, and a synthesis-oriented retrieval path.

### Public endpoints currently documented

- `POST /jobs`
- `GET /jobs/{id}`
- `GET /search`
- `GET /health`

### Architectural implications for the SDK

Although the backend uses an asynchronous job pipeline internally, the SDK should present a **developer-friendly blocking interface** for common usage. That means the SDK should:

1. Submit a job.
2. Poll job status automatically.
3. Return the completed job result when ready.
4. Surface timeout and partial-failure states clearly.

This keeps the SDK simple for application developers while remaining faithful to the backend's job-based design.

---

## SDK Goals

The SDK should satisfy the following design goals:

- **Easy onboarding**: a developer installs the package, provides `apiKey`, and starts using it.
- **Strong typing**: all request/response shapes should be represented with TypeScript interfaces.
- **Safe defaults**: built-in retries, timeout handling, API key validation, and clear errors.
- **Flexible usage**: support high-level blocking calls and low-level direct endpoint wrappers.
- **Framework-agnostic**: work in Node.js, modern frontend apps, and server-side TypeScript projects when appropriate.
- **Open-source quality**: strong package structure, documentation, examples, tests, and semantic versioning.

---

## Recommended Package Name

Choose one of these naming styles and keep the naming consistent across GitHub, npm, and docs:

- `credenceai-sdk`
- `@credenceai/sdk`
- `@credenceai/client`

Recommended npm package name:

```text
@credenceai/sdk
```

Recommended exported client name:

```ts
CredenceAIClient
```

---

## Expected Developer Experience

A consuming project should use the SDK like this:

```ts
import { CredenceAIClient } from "@credenceai/sdk";

const client = new CredenceAIClient({
  apiKey: process.env.CREDENCEAI_API_KEY!,
  baseUrl: "https://api.example.com",
});

const result = await client.run("latest quantum cryptography benchmarks");
console.log(result);
```

The SDK must require the API key during initialization or through environment-driven initialization helpers.

---

## Authentication Design

### Required behavior

Any project using the SDK must provide your API key before accessing services.

### API key rules

- Source of truth: issued by **your backend**
- Format pattern: `cred_sk_...`
- Transport: request header `X-API-Key`
- SDK behavior: reject missing or clearly invalid keys before making network requests

### Recommended auth contract

Every outgoing request should include:

```http
X-API-Key: cred_sk_xxxxxxxxxxxxx
Content-Type: application/json
Accept: application/json
```

### Client-side validation

The SDK should validate:

- key exists
- key is a string
- key starts with `cred_sk_`
- key length is above a safe minimum threshold

Example helper:

```ts
function validateApiKey(apiKey: string): void {
  if (!apiKey || typeof apiKey !== "string") {
    throw new AuthenticationError("Missing API key. Provide a valid CredenceAI API key.");
  }

  if (!apiKey.startsWith("cred_sk_")) {
    throw new AuthenticationError("Invalid API key format. Expected key starting with 'cred_sk_'.");
  }

  if (apiKey.length < 16) {
    throw new AuthenticationError("API key appears too short to be valid.");
  }
}
```

### Environment integration

Provide a convenience factory so any project environment can pass the key from env variables.

Recommended variable name:

```text
CREDENCEAI_API_KEY
```

Optional helper:

```ts
const client = CredenceAIClient.fromEnv({
  baseUrl: process.env.CREDENCEAI_BASE_URL,
});
```

This helper should throw a descriptive error if `CREDENCEAI_API_KEY` is absent.

---

## SDK Surface Design

The SDK should expose both:

1. **Low-level endpoint wrappers** for full control.
2. **A high-level blocking abstraction** for standard usage.

### Public methods

```ts
class CredenceAIClient {
  constructor(config: CredenceAIConfig);

  health(): Promise<HealthResponse>;
  createJob(request: CreateJobRequest): Promise<CreateJobResponse>;
  getJob(jobId: string): Promise<JobStatusResponse>;
  search(params: SearchQueryParams): Promise<SearchResponse>;

  run(query: string, options?: RunOptions): Promise<RunResult>;
}
```

### Method responsibilities

- `health()` wraps `GET /health`
- `createJob()` wraps `POST /jobs`
- `getJob(jobId)` wraps `GET /jobs/{id}`
- `search()` wraps `GET /search`
- `run()` provides the blocking-style abstraction by creating a job and polling until completion

---

## Recommended Folder Structure

```text
credenceai-sdk/
├── src/
│   ├── index.ts
│   ├── client.ts
│   ├── config.ts
│   ├── constants.ts
│   ├── errors.ts
│   ├── types/
│   │   ├── common.ts
│   │   ├── config.ts
│   │   ├── jobs.ts
│   │   ├── search.ts
│   │   └── health.ts
│   ├── core/
│   │   ├── http.ts
│   │   ├── auth.ts
│   │   ├── polling.ts
│   │   ├── validation.ts
│   │   └── serializer.ts
│   ├── services/
│   │   ├── jobs.ts
│   │   ├── search.ts
│   │   └── health.ts
│   └── utils/
│       ├── env.ts
│       ├── timing.ts
│       └── guards.ts
├── examples/
│   ├── node-basic.ts
│   ├── run-query.ts
│   └── search-direct.ts
├── test/
│   ├── client.test.ts
│   ├── auth.test.ts
│   ├── polling.test.ts
│   └── mocks/
├── package.json
├── tsconfig.json
├── tsup.config.ts
├── vitest.config.ts
├── README.md
├── LICENSE
└── .gitignore
```

This structure keeps transport, business logic, types, and convenience layers clearly separated.

---

## Core Types

### Config

```ts
export interface CredenceAIConfig {
  apiKey: string;
  baseUrl: string;
  timeoutMs?: number;
  pollIntervalMs?: number;
  maxWaitMs?: number;
  userAgent?: string;
  fetch?: typeof globalThis.fetch;
}
```

### Common API response envelope

If your backend already uses a shared response structure, the SDK should mirror it. If not, define internal normalization types so SDK users always receive predictable objects.

```ts
export interface ApiErrorPayload {
  message: string;
  code?: string;
  details?: unknown;
}
```

### Jobs

```ts
export interface CreateJobRequest {
  query: string;
  intent?: "news" | "company" | "research" | "web" | string;
  mode?: "fast" | "standard" | "deep" | string;
  metadata?: Record<string, unknown>;
}

export interface CreateJobResponse {
  job_id: string;
  status: string;
  trace_id?: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed" | string;
  result?: unknown;
  error?: ApiErrorPayload;
  trace_id?: string;
}
```

### Search

```ts
export interface SearchQueryParams {
  q: string;
  limit?: number;
  offset?: number;
  intent?: string;
}

export interface SearchResultItem {
  title?: string;
  url?: string;
  snippet?: string;
  source?: string;
  score?: number;
  metadata?: Record<string, unknown>;
}

export interface SearchResponse {
  query: string;
  results: SearchResultItem[];
  total?: number;
}
```

### Health

```ts
export interface HealthResponse {
  status: string;
  version?: string;
  dependencies?: Record<string, string>;
}
```

### Blocking abstraction

```ts
export interface RunOptions {
  intent?: string;
  mode?: string;
  pollIntervalMs?: number;
  maxWaitMs?: number;
  metadata?: Record<string, unknown>;
}

export interface RunResult {
  jobId: string;
  status: string;
  data: unknown;
  traceId?: string;
}
```

---

## Client Class Design

```ts
export class CredenceAIClient {
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly timeoutMs: number;
  private readonly pollIntervalMs: number;
  private readonly maxWaitMs: number;
  private readonly http: HttpClient;

  constructor(config: CredenceAIConfig) {
    validateApiKey(config.apiKey);
    this.apiKey = config.apiKey;
    this.baseUrl = normalizeBaseUrl(config.baseUrl);
    this.timeoutMs = config.timeoutMs ?? 30000;
    this.pollIntervalMs = config.pollIntervalMs ?? 1500;
    this.maxWaitMs = config.maxWaitMs ?? 120000;
    this.http = new HttpClient({
      baseUrl: this.baseUrl,
      apiKey: this.apiKey,
      timeoutMs: this.timeoutMs,
      fetchImpl: config.fetch,
      userAgent: config.userAgent,
    });
  }

  static fromEnv(opts: { baseUrl?: string } = {}) {
    const apiKey = process.env.CREDENCEAI_API_KEY;
    const baseUrl = opts.baseUrl ?? process.env.CREDENCEAI_BASE_URL;

    if (!apiKey) {
      throw new AuthenticationError("Missing CREDENCEAI_API_KEY environment variable.");
    }

    if (!baseUrl) {
      throw new ConfigurationError("Missing CredenceAI baseUrl. Provide it directly or via CREDENCEAI_BASE_URL.");
    }

    return new CredenceAIClient({ apiKey, baseUrl });
  }
}
```

---

## HTTP Layer

The SDK should centralize all network behavior in a reusable internal HTTP client.

### Responsibilities

- add `X-API-Key` automatically
- set default headers
- handle timeouts
- parse JSON safely
- normalize backend errors into SDK-specific exceptions
- optionally attach trace IDs from response headers

### Suggested internal interface

```ts
interface HttpRequestOptions {
  method: "GET" | "POST";
  path: string;
  query?: Record<string, string | number | boolean | undefined>;
  body?: unknown;
  signal?: AbortSignal;
}
```

### Header strategy

```ts
const headers = {
  "Content-Type": "application/json",
  Accept: "application/json",
  "X-API-Key": apiKey,
  "User-Agent": userAgent ?? "@credenceai/sdk",
};
```

---

## Endpoint Wrapper Design

### 1. Health API

```ts
async health(): Promise<HealthResponse> {
  return this.http.request<HealthResponse>({
    method: "GET",
    path: "/health",
  });
}
```

### 2. Create Job API

```ts
async createJob(request: CreateJobRequest): Promise<CreateJobResponse> {
  if (!request?.query?.trim()) {
    throw new ValidationError("createJob requires a non-empty query.");
  }

  return this.http.request<CreateJobResponse>({
    method: "POST",
    path: "/jobs",
    body: request,
  });
}
```

### 3. Get Job API

```ts
async getJob(jobId: string): Promise<JobStatusResponse> {
  if (!jobId?.trim()) {
    throw new ValidationError("getJob requires a valid jobId.");
  }

  return this.http.request<JobStatusResponse>({
    method: "GET",
    path: `/jobs/${encodeURIComponent(jobId)}`,
  });
}
```

### 4. Search API

```ts
async search(params: SearchQueryParams): Promise<SearchResponse> {
  if (!params?.q?.trim()) {
    throw new ValidationError("search requires a non-empty q parameter.");
  }

  return this.http.request<SearchResponse>({
    method: "GET",
    path: "/search",
    query: {
      q: params.q,
      limit: params.limit,
      offset: params.offset,
      intent: params.intent,
    },
  });
}
```

---

## Blocking-Style Abstraction

This is the most important SDK feature because your backend is job-driven while the desired SDK experience is simple and synchronous from the developer's perspective.

### Behavior of `run()`

`run()` should:

1. call `createJob()`
2. extract `job_id`
3. poll `getJob(job_id)` on a fixed interval
4. stop when status becomes `completed`
5. throw when status becomes `failed`
6. throw timeout error if the job exceeds `maxWaitMs`

### Example implementation shape

```ts
async run(query: string, options: RunOptions = {}): Promise<RunResult> {
  const job = await this.createJob({
    query,
    intent: options.intent,
    mode: options.mode,
    metadata: options.metadata,
  });

  const pollIntervalMs = options.pollIntervalMs ?? this.pollIntervalMs;
  const maxWaitMs = options.maxWaitMs ?? this.maxWaitMs;
  const startedAt = Date.now();

  while (Date.now() - startedAt < maxWaitMs) {
    const status = await this.getJob(job.job_id);

    if (status.status === "completed") {
      return {
        jobId: status.job_id,
        status: status.status,
        data: status.result,
        traceId: status.trace_id,
      };
    }

    if (status.status === "failed") {
      throw new JobFailedError(
        status.error?.message ?? "CredenceAI job failed.",
        { jobId: status.job_id, payload: status }
      );
    }

    await sleep(pollIntervalMs);
  }

  throw new TimeoutError("CredenceAI job polling exceeded max wait time.", {
    query,
    maxWaitMs,
  });
}
```

### Optional enhancement

Support a customizable completion predicate so future backend status names can be adopted without changing public API behavior.

---

## Error Model

A clean SDK needs a strong error hierarchy.

### Recommended errors

```ts
export class CredenceAIError extends Error {}
export class ConfigurationError extends CredenceAIError {}
export class AuthenticationError extends CredenceAIError {}
export class ValidationError extends CredenceAIError {}
export class ApiError extends CredenceAIError {
  statusCode?: number;
  traceId?: string;
  details?: unknown;
}
export class TimeoutError extends CredenceAIError {
  details?: unknown;
}
export class JobFailedError extends CredenceAIError {
  details?: unknown;
}
export class RateLimitError extends ApiError {}
export class NetworkError extends CredenceAIError {}
```

### Mapping guidance

- `401` or `403` -> `AuthenticationError`
- `400` or validation issues -> `ValidationError`
- `404` -> `ApiError`
- `429` -> `RateLimitError`
- `5xx` -> `ApiError`
- fetch/network failures -> `NetworkError`
- polling timeout -> `TimeoutError`
- terminal job failure -> `JobFailedError`

---

## Input Validation Rules

The SDK should validate client-side where possible.

### Validate at initialization

- `apiKey`
- `baseUrl`
- timeout values must be positive numbers
- poll interval must be reasonable

### Validate per method

- `query` must be non-empty
- `jobId` must be non-empty
- `limit` and `offset` must be numeric and non-negative

This reduces avoidable round-trips and improves developer feedback.

---

## Base URL Strategy

The SDK should not hardcode environments. Instead, it should require or accept `baseUrl`.

### Recommended environments

- local: `http://127.0.0.1:8000`
- staging: `https://staging-api.yourdomain.com`
- production: `https://api.yourdomain.com`

### Normalization rule

Strip trailing slashes so endpoint composition is predictable.

```ts
function normalizeBaseUrl(baseUrl: string): string {
  return baseUrl.replace(/\/+$/, "");
}
```

---

## Response Normalization

Your backend may evolve over time, so the SDK should shield consumers from inconsistent shapes where possible.

### Recommendation

Create internal mappers such as:

- `mapJobResponse()`
- `mapSearchResponse()`
- `mapHealthResponse()`

This gives you a stable SDK contract even if backend fields are renamed or expanded later.

---

## Traceability Support

The project documentation mentions trace-ID middleware and request correlation. The SDK should preserve that value whenever available.

### Recommendation

- extract `trace_id` from response body when present
- optionally extract a trace header if the backend exposes one later
- attach trace IDs to thrown SDK errors when available

This makes debugging much easier for consumers and maintainers.

---

## Retry Policy

Not every request should retry automatically.

### Safe default retries

Retry only for:

- transient network failures
- `502`, `503`, `504`
- optional `429` with backoff if your backend rate-limits clients

### Do not auto-retry

- authentication failures
- validation failures
- completed job retrieval failures caused by bad IDs

### Recommended defaults

- retry count: `2`
- backoff: exponential, starting at `500ms`
- jitter: enabled

---

## Packaging Recommendations

### Tooling

Recommended modern TypeScript package stack:

- `typescript`
- `tsup` for build output
- `vitest` for tests
- `eslint`
- `prettier`
- `@types/node`

### Output formats

Publish both:

- ESM
- CommonJS
- Type declaration files

### Suggested `package.json` direction

```json
{
  "name": "@credenceai/sdk",
  "version": "0.1.0",
  "type": "module",
  "main": "./dist/index.cjs",
  "module": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "import": "./dist/index.js",
      "require": "./dist/index.cjs"
    }
  }
}
```

---

## README Requirements for the SDK Repo

The SDK repository README should include:

1. what CredenceAI SDK does
2. install command
3. API key setup
4. quick start example
5. endpoint-level examples
6. blocking `run()` example
7. error handling example
8. environment variable usage
9. local development instructions
10. contribution guidelines

### Example install section

```bash
npm install @credenceai/sdk
```

### Example env section

```bash
export CREDENCEAI_API_KEY=cred_sk_your_key_here
export CREDENCEAI_BASE_URL=https://api.yourdomain.com
```

---

## Example Usage Snippets

### High-level blocking usage

```ts
import { CredenceAIClient } from "@credenceai/sdk";

const client = CredenceAIClient.fromEnv();

const result = await client.run("federated learning privacy benchmarks", {
  mode: "standard",
  maxWaitMs: 60000,
});

console.log(result.data);
```

### Direct job control

```ts
const job = await client.createJob({
  query: "agentic AI system design",
  mode: "deep",
});

const status = await client.getJob(job.job_id);
console.log(status.status);
```

### Direct search usage

```ts
const response = await client.search({
  q: "blockchain governance models",
  limit: 10,
});

console.log(response.results);
```

### Health check

```ts
const health = await client.health();
console.log(health.status);
```

---

## Testing Plan

The SDK should include unit tests, integration tests, and mocked transport tests.

### Unit tests

- API key validation
- base URL normalization
- query parameter serialization
- error mapping
- polling timeout behavior

### Integration tests

- health endpoint call
- job creation call
- polling completion flow
- search endpoint call
- authentication header injection

### Mocking strategy

Use mocked `fetch` responses for deterministic SDK tests. Add optional live integration tests behind environment flags.

---

## Versioning Strategy

Because the backend is still evolving, the SDK should begin with clear semantic versioning.

### Recommendation

- `0.x` while backend contracts are still changing rapidly
- `1.0.0` after endpoint contracts stabilize

### Compatibility policy

Document which backend version range the SDK supports. Example:

```text
SDK 0.1.x supports CredenceAI backend MVP / iteration 0.1+
```

---

## Security Notes

The SDK should not expose or log API keys.

### Required practices

- never print full API keys in logs
- redact keys in debug output
- do not store keys automatically
- allow users to supply keys via env or runtime config
- avoid embedding secrets in browser-distributed sample apps

### Redaction example

```ts
function redactApiKey(apiKey: string): string {
  return apiKey.length <= 10
    ? "[REDACTED]"
    : `${apiKey.slice(0, 7)}...${apiKey.slice(-4)}`;
}
```

---

## Browser vs Server Consideration

Since the SDK target is JavaScript/TypeScript, decide whether browser use is officially supported.

### Recommended position

Support **Node.js first** and allow browser use only if:

- CORS is correctly configured on your API
- exposing client-side API keys is acceptable for your product model
- rate limits and abuse protections are in place

If browser usage is sensitive, document that the SDK is primarily for **server-side integration**.

---

## Suggested Implementation Order

Build the SDK in the following sequence:

1. create package scaffold
2. define TypeScript interfaces
3. build auth validation and config loader
4. implement internal HTTP client
5. wrap `/health`
6. wrap `/jobs`
7. wrap `/jobs/{id}`
8. wrap `/search`
9. implement blocking `run()` polling abstraction
10. implement error mapping
11. add tests
12. write README and examples
13. publish initial npm release

This order minimizes integration risk and gets a usable SDK running quickly.

---

## Recommended Initial Public API

```ts
export {
  CredenceAIClient,
  CredenceAIError,
  ConfigurationError,
  AuthenticationError,
  ValidationError,
  ApiError,
  TimeoutError,
  JobFailedError,
  RateLimitError,
  NetworkError,
};

export type {
  CredenceAIConfig,
  CreateJobRequest,
  CreateJobResponse,
  JobStatusResponse,
  SearchQueryParams,
  SearchResponse,
  SearchResultItem,
  HealthResponse,
  RunOptions,
  RunResult,
};
```

---

## Notes on Backend Alignment

The current backend documents a FastAPI gateway, job submission/status endpoints, search endpoint, health endpoint, trace-aware middleware, and an async worker-oriented execution model. The SDK design above intentionally matches that shape without forcing external developers to manually manage asynchronous orchestration details.

It also aligns with the broader architecture in which requests move through intent classification, orchestration, crawling/extraction, storage/indexing, and synthesis stages behind the API boundary. That means the SDK should stay thin, stable, typed, and transport-focused rather than re-implementing backend intelligence on the client side.

---

## Final Recommendation

The best implementation approach is to build a **thin TypeScript client SDK** with:

- strict config validation
- mandatory API key injection through `X-API-Key`
- wrappers for all four documented endpoints
- one high-level `run()` blocking abstraction
- strong error typing
- environment-based initialization helpers
- open-source-ready packaging and tests

This gives external developers a clean integration experience while preserving compatibility with the CredenceAI backend's current architecture and future growth.
