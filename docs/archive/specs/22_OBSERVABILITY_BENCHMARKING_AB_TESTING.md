# Observability, Benchmarking, and A/B Testing

## Observability Metrics

```text
provider_success_rate
provider_error_rate
provider_timeout_rate
provider_latency_p95
provider_duplicate_rate
provider_freshness_score
crawl_success_rate
crawl_failure_rate
crawl_robots_block_rate
browser_cpu_seconds_per_page
extraction_success_rate
entity_match_rate
entity_conflict_rate
duplicate_rate
quality_rejection_rate
manual_review_rate
kafka_lag_by_topic
dead_letter_count
postgres_write_latency
minio_write_latency
opensearch_index_latency
cache_hit_rate
cost_per_query
```

## Dashboards

| Dashboard | Shows |
|---|---|
| Provider Health | Success, errors, latency, freshness, usefulness. |
| Crawl Operations | Crawl success, robots blocks, retries, browser cost. |
| Data Quality | Trust scores, rejection rate, duplicate rate. |
| Entity Resolution | Match rate, conflicts, ambiguity. |
| A/B Experiment | Variants, metrics, significance, winner. |
| Benchmark | Precision, freshness, latency, cost trends. |
| DLQ | Failed events, retries, error types. |
| Cost and Resource | CPU, storage, LLM calls, browser usage. |
| Security and Compliance | SSRF blocks, MIME rejects, policy denials. |

## Benchmark Datasets

Create labeled datasets for:

- General web queries.
- Ambiguous entity queries.
- Company/entity queries.
- News/event queries.
- Scholarly queries.
- Historical URL queries.
- Multilingual queries.
- Media-heavy queries.
- High-risk crawling queries.
- RAG document collection.
- Risk/compliance monitoring.

## Benchmark Metrics

| Area | Metric |
|---|---|
| Search quality | top_10_precision, nDCG, MRR. |
| Deduplication | duplicate suppression rate, false merge rate. |
| Freshness | median source age, freshness hit rate. |
| Crawling | crawl success rate, robots block rate. |
| Extraction | valid extraction rate, boilerplate rate. |
| Entity resolution | precision, recall, ambiguity error rate. |
| Metadata | metadata completeness, conflict rate. |
| Latency | p50, p95, p99. |
| Efficiency | source calls/query, crawl cost/query, LLM calls/query. |
| Trust | evidence coverage, citation accuracy, source reliability. |
| RAG quality | answer faithfulness, retrieval relevance, chunk usefulness. |

## Core A/B Experiments

### Experiment 1: SearXNG Only vs SearXNG + Enrichment

| Variant | Pipeline |
|---|---|
| A | SearXNG only |
| B | SearXNG + Wikidata + GDELT + Common Crawl |

Success:

- Relevance improves by at least 10%.
- Duplicate rate drops by at least 15%.
- Latency increase remains acceptable.

### Experiment 2: Scrapy Only vs Scrapy + Playwright Fallback

Success:

- Extraction success improves by at least 20%.
- Browser CPU cost remains below threshold.

### Experiment 3: Live Crawl vs Common Crawl First

Success:

- Live crawl volume drops by at least 30%.
- Freshness loss remains acceptable.

### Experiment 4: OpenAlex Only vs OpenAlex + Crossref + arXiv

Success:

- Metadata completeness improves by at least 20%.
- Conflicts are measurable and resolvable.

### Experiment 5: Free Sources vs Paid SERP

Success:

- Quality improves by at least 15%, or failure rate drops by at least 30%, or critical-query success improves significantly.

## Benchmark Baselines

Compare against:

- SearXNG only.
- AI search API style output.
- OpenSearch over raw crawled data.
- GDELT only for news.
- OpenAlex only for scholarly.
- Manual analyst workflow.

## Experiment Decision Policy

Do not adopt variant B unless it improves target metrics without unacceptable cost, latency, or review burden.
