# Product Requirements

## Product Objective

Build a modular, self-hostable, free-first intelligence platform that discovers, validates, enriches, crawls, extracts, indexes, and monitors trusted public data.

## Core Product Promise

CredenceAI should transform raw public information into trusted searchable intelligence.

Raw data may be stored for audit and replay, but only scored, deduplicated, policy-approved, extracted, and validated data should become trusted search or AI context.

## Primary User Personas

| Persona | Need | Success outcome |
|---|---|---|
| Analyst | Fast evidence-backed intelligence | Clear summaries, source tables, confidence scores. |
| AI engineer | RAG-ready trusted documents | Clean chunks, citations, metadata, embeddings. |
| Researcher | Structured research collections | Paper/source/entity maps and conflict reports. |
| Risk/compliance user | Auditable public monitoring | Alerts, evidence, source provenance, review workflows. |
| Product builder | Search intelligence API | Scored results, entity cards, exportable datasets. |

## Supported Job Types

```text
search_query
entity_lookup
url_crawl
news_monitoring
scholarly_search
media_discovery
archive_lookup
geo_lookup
competitor_monitoring
brand_monitoring
risk_monitoring
research_collection
dataset_building
rag_dataset_builder
intelligence_card_request
summary_request
```

## Functional Requirements

### Job intake

- Accept jobs through REST API, UI, CLI/SDK, scheduler, and webhook integrations.
- Validate job payloads.
- Assign priority, deadline, execution mode, routing mode, and trace ID.
- Store job state transitions.

### Intent classification

- Classify query intent.
- Detect entities, language, vertical, freshness requirement, crawl requirement, and risk level.
- Suggest source plan and job plan.

### Source orchestration

- Route to free/open sources first.
- Avoid unnecessary source calls.
- Apply source budgets and provider health signals.
- Support optional paid sources only when enabled and justified.

### Normalization

- Convert all source outputs into a common schema.
- Store raw payload references.
- Validate schema contracts.
- Reject malformed outputs to DLQ when required.

### Quality and trust

- Calculate component scores.
- Produce final trust score and decision.
- Preserve decision reasons.
- Apply thresholds by use case.

### Deduplication

- Normalize URLs.
- Strip tracking parameters.
- Canonicalize URLs.
- Group exact and near duplicates.
- Prevent duplicate crawling and indexing.

### Entity resolution

- Generate candidates.
- Use aliases, external IDs, context, source evidence, and official domains.
- Link entities with confidence levels.
- Send ambiguous cases to review or AI-assisted resolution.

### Crawling and extraction

- Enforce crawl policy before crawling.
- Use Scrapy for static pages.
- Use Playwright only as fallback for high-value JS pages.
- Extract title, main text, metadata, language, links, media, structured data, and hashes.

### Evidence and intelligence outputs

- Build evidence objects and entity cards.
- Support source-backed summaries.
- Export RAG-ready datasets.
- Provide confidence and provenance.

### Benchmarking

- Run benchmark datasets.
- Track precision, freshness, latency, duplicate rate, extraction success, and cost.
- Run A/B tests for architecture changes.

## Non-Functional Requirements

| Category | Requirement |
|---|---|
| Accuracy | Trust scores must be calibrated with benchmark data. |
| Latency | Fast mode should answer from cache/index in 1 to 3 seconds. |
| Cost | Free/open sources should be preferred by default. |
| Reliability | Failed jobs should be retriable and visible in DLQ. |
| Security | SSRF, private IP, MIME, file-size, and source-term controls are mandatory. |
| Auditability | Every trusted result must preserve provenance and decision history. |
| Scalability | Workers should scale independently by queue/topic. |
| Maintainability | Source adapters must be stateless and contract-tested. |
| Extensibility | New vertical packs and sources should be pluggable. |

## Out of Scope for Early Iterations

- Full autonomous crawling across large domains.
- Heritrix/Nutch production-grade archival crawling.
- Advanced multimedia intelligence.
- Paid SERP as primary source.
- Fully autonomous AI agent decision-making.
- Legal/medical/financial decision automation without domain-specific governance.
