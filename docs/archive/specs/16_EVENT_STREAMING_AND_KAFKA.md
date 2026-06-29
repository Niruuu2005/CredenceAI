# Event Streaming and Kafka

## Event-Driven Principle

CredenceAI should use event streaming for asynchronous, scalable, and replayable workflows. Events must be idempotent and traceable.

## Topic Map

```text
job-submitted
intent-classified
source-requests
source-results-raw
source-results-normalized
quality-scored-results
dedup-requests
dedup-results
entity-resolution-requests
entity-resolution-results
ai-critic-requests
ai-critic-results
crawl-policy-requests
crawl-policy-results
crawl-requests-static
crawl-requests-browser
crawl-requests-archive
crawl-results
document-extraction-requests
document-extraction-results
media-requests
media-results
indexing-requests
indexing-results
benchmark-events
ab-test-events
agent-decisions
dead-letter-events
```

## Standard Event Envelope

```json
{
  "event_id": "evt_123",
  "event_type": "source.results.normalized",
  "trace_id": "trace_abc",
  "job_id": "job_123",
  "schema_version = "v0.1",
  "occurred_at": "2026-06-16T00:00:00Z",
  "producer": "source-normalizer",
  "payload": {}
}
```

## Idempotency

Every consumer must use idempotency keys.

Recommended keys:

| Event | Idempotency key |
|---|---|
| job-submitted | job_id |
| source request | job_id + source + input_hash |
| crawl request | canonical_url + crawl_policy_decision_id |
| indexing request | document_id + content_hash |
| entity link | entity_id + result_id + mention_hash |

## Retry Policy

| Error type | Retry behavior |
|---|---|
| Timeout | Retry with exponential backoff. |
| 429/rate limited | Backoff and reduce provider/domain weight. |
| Schema validation error | Send to DLQ after raw payload stored. |
| Policy denial | Do not retry. |
| Private IP/SSRF risk | Do not retry; alert if suspicious. |
| Extractor failure | Retry alternate extractor only if high value. |

## Dead Letter Queue

DLQ events must include:

- Original event envelope.
- Error code.
- Error message.
- Component name.
- Retry count.
- Raw payload reference if available.
- Suggested remediation.

## Ordering Rules

Ordering is required within:

- Single job lifecycle.
- Single URL crawl chain.
- Single document indexing chain.
- Single experiment assignment.

Ordering is not required across unrelated jobs.

## Consumer Groups

| Consumer group | Topics |
|---|---|
| intent-workers | job-submitted |
| source-workers | source-requests |
| normalization-workers | source-results-raw |
| quality-workers | source-results-normalized |
| dedup-workers | quality-scored-results |
| entity-workers | dedup-results |
| crawl-policy-workers | entity-resolution-results |
| crawl-workers-static | crawl-requests-static |
| crawl-workers-browser | crawl-requests-browser |
| extraction-workers | crawl-results |
| indexing-workers | document-extraction-results |
| benchmark-workers | benchmark-events |
| agent-workers | ai-critic-requests |
