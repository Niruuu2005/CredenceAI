# Test Plan and Acceptance

## Test Strategy

CredenceAI needs unit tests, integration tests, contract tests, security tests, benchmark tests, and end-to-end acceptance tests.

## Unit Tests

| Module | Tests |
|---|---|
| Intent Classifier | Intent labels, language detection, vertical routing. |
| URL Canonicalizer | Tracking parameter removal, case normalization, redirects. |
| Quality Scorer | Component scores, threshold decisions. |
| Dedup Worker | Exact URL, canonical URL, content hash, near-duplicate matching. |
| Entity Resolver | Alias matching, context matching, confidence thresholds. |
| Crawl Policy | robots, private IP, MIME, file size, rate limit. |
| Extractor | Title/text/metadata/language/hash extraction. |

## Adapter Contract Tests

Every source adapter must test:

- Success response.
- Empty response.
- Malformed response.
- Timeout.
- Rate limit.
- Schema change.
- Raw payload storage.
- Normalized envelope validation.

## Integration Tests

| Flow | Expected result |
|---|---|
| Job to SearXNG to index | Results searchable. |
| Entity lookup | Canonical entity returned. |
| Quality scoring and dedup | Duplicate groups created. |
| Crawl policy allowed | Crawl job emitted. |
| Crawl policy denied | No crawl performed. |
| Extraction to index | Document searchable. |
| Agent validation | Agent decision logged. |

## Security Tests

- Private IP URL blocked.
- Private IP redirect blocked.
- Oversized file blocked.
- MIME mismatch rejected.
- robots.txt disallow respected.
- Executable file quarantined.
- Secrets redacted from logs.

## Benchmark Tests

Benchmark datasets should include:

- General search queries.
- Ambiguous entities.
- Company monitoring.
- News monitoring.
- Scholarly search.
- Crawling and extraction.
- RAG dataset generation.

Metrics:

- top_10_precision.
- duplicate_rate.
- entity_resolution_accuracy.
- extraction_success_rate.
- p95 latency.
- cost per query.
- evidence coverage.

## Iteration Acceptance Gates

### Iteration 0.1

- 100 test queries end-to-end.
- At least 90% normalization success.
- Search API returns indexed results.
- Failed jobs visible.

### Iteration 0.2

- At least 80% obvious duplicate suppression.
- At least 75% basic entity resolution accuracy.
- Every result has quality score and decision.

### Iteration 0.3

- 100% crawls pass policy service.
- Zero private IP crawls allowed.
- At least 80% extraction success on static pages.

### Iteration 0.4

- Agent decisions logged for all AI-assisted cases.
- Evidence-backed summaries available.
- At least two vertical packs work end-to-end.

### Iteration 0.5

- Fast mode p95 under 3 seconds for cached/indexed queries.
- Standard mode p95 under 20 seconds.
- A/B testing operational.
- Provider health and DLQ dashboards operational.

## Release Criteria

Do not release an iteration unless:

- Required tests pass.
- Security gates pass.
- Observability exists for new components.
- Failure mode is visible.
- Documentation is updated.
- Known limitations are recorded.
