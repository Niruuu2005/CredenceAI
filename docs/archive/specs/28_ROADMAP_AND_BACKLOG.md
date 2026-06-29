# Roadmap and Backlog

## Phase 0: Architecture Freeze

Deliverables:

- Source contracts.
- Normalized schemas.
- Event topic map.
- Database schema.
- Routing policy.
- Quality scoring spec.
- Crawl policy spec.
- Agent decision schema.
- Benchmark plan.

Exit criteria:

- Critical schemas defined.
- Service boundaries clear.
- MVP scope frozen.

## Phase 1: Core Free-First MVP

Build:

- Job API.
- Basic Intent Classifier.
- Source Orchestrator.
- SearXNG Adapter.
- Source Normalizer.
- Postgres.
- MinIO.
- OpenSearch.
- Basic result API.

## Phase 2: Trust Layer

Build:

- Quality Scorer.
- Dedup Worker.
- URL Canonicalizer.
- Wikidata/Wikipedia adapters.
- Basic Entity Resolver.
- Source Reliability Registry.

## Phase 3: Crawling and Extraction

Build:

- Crawl Policy Service.
- Scrapy Worker.
- Common Crawl Adapter.
- Extraction Processor.
- Freshness Scoring.
- Content Hash Store.

## Phase 4: Agentic and Intelligence Outputs

Build:

- Planner Agent.
- Source Selection Agent.
- Quality Critic Agent.
- Entity Resolution Agent.
- Extraction Validation Agent.
- Evidence Graph.
- Intelligence Cards.
- Vertical Packs.

## Phase 5: Production Optimization

Build:

- Fast/Standard/Deep modes.
- Latency-Aware Planner.
- Cache Manager.
- Hybrid Retrieval.
- Reranker.
- Benchmark Runner.
- A/B Test Router.
- Observability dashboards.
- Admin Review Queue.
- Cost/Quota Manager.

## Priority Backlog

### Critical

- Source contracts.
- Source orchestrator.
- Source normalizer.
- Quality scorer.
- Dedup worker.
- Crawl policy service.
- DLQ and retry logic.
- Benchmark dataset.
- Provider health monitor.

### High Priority

- Entity resolver.
- OpenSearch indexing.
- Admin review UI.
- Observability dashboards.
- Agent decision logging.
- Source confidence scoring.

### Medium Priority

- Playwright fallback.
- Common Crawl first strategy.
- A/B test router.
- Scholarly adapters.
- AI critic agent.
- Ops recovery agent.

### Low Priority

- Paid SERP APIs.
- Heritrix.
- Self-hosted Nominatim.
- Nutch.
- Advanced media intelligence.

## Suggested First Vertical Pack

Start with either:

1. Company Intelligence Pack, because business value is clear.
2. RAG Dataset Builder Pack, because AI teams urgently need trusted data.

Do not build all verticals at once. That is not ambition; that is scope debt with branding.
