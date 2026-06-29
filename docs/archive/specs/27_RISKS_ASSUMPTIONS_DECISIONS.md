# Risks, Assumptions, and Decisions

## Key Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Scope explosion | Delayed delivery | Use five-iteration plan and vertical packs. |
| Low source quality | Bad results | Source reliability registry and benchmarks. |
| Entity false merges | Polluted intelligence | Confidence thresholds and review queue. |
| Crawling compliance issues | Legal/security exposure | Deterministic crawl policy and audit logs. |
| High browser cost | Infrastructure waste | Playwright fallback only and budget manager. |
| AI hallucination | Incorrect summaries/decisions | Evidence-backed outputs and logged agent decisions. |
| Paid API dependency | Cost/vendor lock-in | Free-first routing and paid only when benchmark-justified. |
| Stale data | Bad intelligence | Freshness scoring and recrawl policy. |
| Storage growth | Cost and operational burden | Retention policy, dedup, compression. |
| Benchmark weakness | False confidence | Labeled datasets and baseline comparisons. |

## Assumptions

- SearXNG is available as the default free-first search provider.
- Postgres, MinIO, OpenSearch, Redis, and Kafka are acceptable platform components.
- Early users value trusted intelligence more than raw search volume.
- Open sources can provide sufficient signal for many use cases.
- Paid SERP APIs are optional and should be justified with benchmark evidence.
- AI agents are useful for ambiguity and synthesis, not deterministic safety decisions.

## Architecture Decisions

| Decision | Rationale |
|---|---|
| Use free-first routing | Controls cost and improves self-hostability. |
| Store raw payloads | Enables audit, replay, debugging. |
| Use OpenSearch | Supports full-text and hybrid search path. |
| Use Postgres | Reliable transactional metadata and decisions. |
| Use MinIO/S3 | Scalable raw and processed object storage. |
| Use Kafka from iteration 0.3/5 depending scale | Enables scalable asynchronous processing. |
| Split Fast/Standard/Deep modes | Prevents deep crawls from ruining interactive latency. |
| Make agents governed | Reduces AI risk and cost. |
| Benchmark all major changes | Prevents opinion-driven architecture. |

## Open Questions

- Which vertical pack should be first for real users: company intelligence or RAG dataset builder?
- What minimum benchmark size is required before changing scoring thresholds?
- Should graph store be Postgres-based initially or separate from the start?
- How much historical content should be retained by default?
- What review workflow is required for compliance-focused deployments?

## Product Kill Gates

Do not ship a feature if:

- Benchmark quality does not improve.
- A/B test fails.
- Manual review load increases too much.
- Latency becomes unacceptable.
- Cost increases without quality gain.
- Compliance risk is unresolved.
