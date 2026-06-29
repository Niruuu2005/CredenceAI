# CredenceAI Client SDK

A robust, typed JavaScript/TypeScript client library for the **CredenceAI search-intelligence API**. 

The SDK provides both a developer-friendly high-level blocking interface (which automatically polls jobs until completion) and low-level wrappers to call individual endpoints directly.

## Installation

```bash
npm install @credenceai/sdk
```

## Setup & Authentication

The SDK requires an API key issued by your own backend. All keys must follow the format `cred_sk_...`.

You can pass the configuration parameters directly during client initialization or load them automatically from the environment variables.

### Environment Variables

Configure the following variables in your environment:

```bash
export CREDENCEAI_API_KEY=cred_sk_your_api_key_here
export CREDENCEAI_BASE_URL=https://api.yourdomain.com
```

Initialize the client using the static factory method:

```typescript
import { CredenceAIClient } from "@credenceai/sdk";

const client = CredenceAIClient.fromEnv();
```

### Manual Configuration

```typescript
import { CredenceAIClient } from "@credenceai/sdk";

const client = new CredenceAIClient({
  apiKey: "cred_sk_your_api_key_here",
  baseUrl: "https://api.yourdomain.com",
  timeoutMs: 30000,       // Request timeout (default 30s)
  pollIntervalMs: 1500,   // Wait between status polls (default 1.5s)
  maxWaitMs: 120000,      // Max polling duration (default 2 mins)
});
```

---

## Usage Guide

### 1. High-Level Blocking Abstraction

The blocking `run()` method is recommended for most applications. It submits a search-intelligence query as a job, polls the status, and returns the result once completed.

```typescript
import { CredenceAIClient } from "@credenceai/sdk";

const client = CredenceAIClient.fromEnv();

try {
  const result = await client.run("latest quantum cryptography benchmarks", {
    mode: "standard", // "fast" | "standard" | "deep"
    intent: "research",
  });
  
  console.log("Job Completed:", result.jobId);
  console.log("Result Data:", result.data);
  console.log("Trace ID:", result.traceId);
} catch (error) {
  console.error("Execution Failed:", error);
}
```

### 2. Low-Level API Endpoint Wrappers

For custom flows, you can interact directly with the asynchronous endpoints:

```typescript
import { CredenceAIClient } from "@credenceai/sdk";

const client = CredenceAIClient.fromEnv();

// 1. Submit a job
const job = await client.createJob({
  query: "agentic AI system design",
  mode: "deep",
});
console.log(`Job Created: ${job.job_id} (Status: ${job.status})`);

// 2. Poll job status manually
const status = await client.getJob(job.job_id);
console.log(`Current Status: ${status.status}`);
if (status.status === "completed") {
  console.log("Result:", status.result);
}
```

### 3. Direct Search API

Use the synchronous search endpoint directly:

```typescript
import { CredenceAIClient } from "@credenceai/sdk";

const client = CredenceAIClient.fromEnv();

const response = await client.search({
  q: "blockchain governance models",
  limit: 10,
});

for (const item of response.results) {
  console.log(`- ${item.title} (${item.url})`);
  console.log(`  Snippet: ${item.snippet}`);
}
```

### 4. Health Check

```typescript
import { CredenceAIClient } from "@credenceai/sdk";

const client = CredenceAIClient.fromEnv();
const health = await client.health();
console.log("API Status:", health.status);
```

---

## Error Handling

The SDK provides a rich hierarchy of typed errors:

```typescript
import { 
  CredenceAIClient, 
  AuthenticationError, 
  ValidationError, 
  TimeoutError, 
  JobFailedError, 
  ApiError 
} from "@credenceai/sdk";

const client = CredenceAIClient.fromEnv();

try {
  await client.run("query text");
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error("Invalid or missing API key format.");
  } else if (error instanceof ValidationError) {
    console.error("Invalid input parameters:", error.message);
  } else if (error instanceof JobFailedError) {
    console.error(`Job ${error.details?.jobId} failed on the worker:`, error.message);
  } else if (error instanceof TimeoutError) {
    console.error("Polling timed out before job finished.");
  } else if (error instanceof ApiError) {
    console.error(`API response failed (${error.statusCode}):`, error.message);
    console.error("Trace ID:", error.traceId);
  } else {
    console.error("Unexpected error:", error);
  }
}
```

---

## Retries and Timeouts

The SDK automatically handles transient failures such as network drops, rate limits (HTTP 429), and gateway issues (HTTP 502, 503, 504) by applying **exponential backoff with jitter** (up to 2 retries).

Validation errors, authentication errors, and terminal job failures are not retried.

---

## Security Considerations

> [!CAUTION]
> This SDK is intended primarily for **server-side integration** (Node.js, edge workers, etc.). 
> Using it directly in browser-based frontend applications exposes your backend API key (`cred_sk_...`) to the client, allowing anyone to inspect network traffic and extract it.
> 
> If you need to make calls from a frontend client, proxy the requests through your own backend server.

---

## Local Development

1. Install dependencies:
   ```bash
   npm install
   ```
2. Build the package (outputs ESM/CommonJS to `dist/`):
   ```bash
   npm run build
   ```
3. Run test suite:
   ```bash
   npm run test
   ```
4. Run examples directly:
   ```bash
   npx tsx examples/node-basic.ts
   ```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
