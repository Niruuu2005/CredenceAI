# Source Adapters

## Adapter Principle

Each source adapter should be small, stateless, contract-tested, and replaceable. It should not contain product logic. Product logic belongs in orchestration, scoring, and validation layers.

## Adapter Responsibilities

1. Receive normalized request.
2. Call source.
3. Store raw payload in MinIO/S3.
4. Emit normalized source envelope.
5. Update provider health metrics.
6. Fail safely with retry/DLQ metadata.

## Adapter Output Contract

```json
{
  "source": "openalex",
  "source_type": "scholarly",
  "input_type": "query",
  "input_value": "transformer attention paper",
  "results": [],
  "raw_payload_ref": "s3://raw/openalex/job_123.json",
  "status": "success",
  "confidence": 0.84,
  "fetched_at": "2026-06-16T00:00:00Z",
  "schema_version = "v0.1"
}
```

## Recommended Adapters

| Adapter | Use | Iteration |
|---|---|---:|
| searxng-adapter | Free-first web search | 1 |
| wikidata-adapter | Entity identity and external IDs | 2 |
| wikipedia-adapter | Entity context and descriptions | 2 |
| gdelt-adapter | News and event discovery | 2/3 |
| commoncrawl-adapter | Historical/low-freshness pages | 3 |
| openalex-adapter | Scholarly works and entities | 3/4 |
| crossref-adapter | DOI and publication metadata | 4 |
| arxiv-adapter | Preprints and versioning | 4 |
| internetarchive-adapter | Historical page snapshots | 4/5 |
| nominatim-adapter | Location/geospatial identity | 5 |
| serpapi-adapter | Optional paid SERP fallback | 5 only if justified |
| valueserp-adapter | Optional paid SERP fallback | 5 only if justified |

## Source Routing Table

| Input type | Primary source | Secondary source | Fallback |
|---|---|---|---|
| General web search | SearXNG | Common Crawl | Paid SERP optional |
| News/events | GDELT | SearXNG news | Live crawl |
| Entity identity | Wikidata | Wikipedia | Manual review |
| Historical page | Common Crawl | Internet Archive | Live crawl |
| Academic paper | OpenAlex | Crossref/arXiv | SearXNG |
| DOI lookup | Crossref | OpenAlex | arXiv |
| Location | Nominatim | Wikidata/OSM | Review |
| URL crawl | Scrapy | Playwright | Common Crawl |

## Provider Health Metrics

Each adapter should report:

- Success rate.
- Error rate.
- Timeout rate.
- Latency p50/p95/p99.
- Duplicate rate.
- Freshness score.
- Useful-result rate.
- Cost per useful result where applicable.

## Contract Tests

Every adapter must have tests for:

- Successful response.
- Empty response.
- Malformed response.
- Timeout.
- Rate limit.
- Schema change.
- Raw payload storage.
- Normalized envelope validation.

## Provider Kill Gates

Downgrade or disable source when:

- Timeout rate exceeds threshold.
- Error rate exceeds threshold.
- Duplicate rate becomes too high.
- Freshness drops below threshold.
- Schema contract fails.
- Quota is exhausted.
- Cost per useful result is too high.
