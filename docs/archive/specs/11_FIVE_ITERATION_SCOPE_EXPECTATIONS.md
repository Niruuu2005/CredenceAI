# Five-Iteration Scope and Expectations

## Development Principle

Each iteration must improve the application incrementally and produce a usable product state. No iteration should exist only to add diagrams, abstraction, or “future-proofing,” which is usually just procrastination wearing a lanyard.

## Summary Table

| Iteration | Main focus | What improves | Main output |
|---:|---|---|---|
| 1 | Core MVP pipeline | Basic functionality | Searchable normalized results |
| 2 | Quality, deduplication, entities | Accuracy and trust | Scored, deduplicated, entity-linked results |
| 3 | Safe crawling and extraction | Coverage and content depth | Crawled, extracted, trusted documents |
| 4 | Agentic validation and intelligence cards | Usefulness and decision quality | Evidence-backed intelligence outputs |
| 5 | Scale, benchmarking, optimization | Speed, efficiency, production readiness | Production-grade measurable platform |

## Iteration 0.1: Core MVP Search Intelligence Pipeline

### Goal

Build the minimum working end-to-end system.

### Scope

- Job API.
- Basic Intent Classifier.
- Source Orchestrator v1.
- SearXNG Adapter.
- Basic Source Normalizer.
- Postgres metadata store.
- MinIO raw payload store.
- OpenSearch index.
- Basic Result API.
- Basic UI/Admin View.

### Expectations

- Accept search jobs.
- Classify basic intent.
- Query SearXNG.
- Normalize results.
- Store raw payloads.
- Store metadata.
- Index searchable results.
- Return results through API.
- Show job status.

### Acceptance Criteria

- 100 test queries can run end-to-end.
- At least 90% normalization success.
- Raw payloads stored for audit.
- Failed jobs visible with error reason.

## Iteration 0.2: Quality Scoring, Deduplication, and Entity Resolution

### Goal

Improve accuracy and trust.

### Scope

- Quality Scoring Layer v1.
- URL Canonicalization.
- Deduplication Worker.
- Wikidata Adapter.
- Wikipedia Adapter.
- Basic Entity Resolver.
- Source Reliability Registry.
- Trust Score Field.
- Evidence Metadata.

### Expectations

- Remove obvious duplicate URLs.
- Strip tracking parameters.
- Score result quality.
- Resolve simple entities.
- Attach confidence scores.
- Reject or downgrade weak results.
- Add source reliability logic.

### Acceptance Criteria

- At least 80% obvious duplicate suppression.
- At least 75% correct entity linking on test set.
- Every result has quality score.
- Every result has Accept/Review/Reject decision.

## Iteration 0.3: Safe Crawling, Extraction, and Freshness

### Goal

Improve coverage and content depth.

### Scope

- Crawl Policy Service.
- Robots.txt checker.
- Domain rate limiting.
- Private IP / SSRF protection.
- Scrapy Worker.
- Document Extractor.
- Content Hashing.
- Extraction Quality Score.
- Common Crawl Adapter.
- Freshness Scoring.
- URL Crawl Cache.

### Expectations

- Crawl only policy-approved URLs.
- Respect robots.txt.
- Block private IP redirects.
- Avoid duplicate crawls.
- Extract title, text, metadata, links, language, and content hash.
- Score extraction quality.
- Use Common Crawl when appropriate.
- Index extracted documents.

### Acceptance Criteria

- At least 70% crawl success for accessible pages.
- 100% crawls pass through policy service.
- Zero private IP crawls allowed.
- At least 80% extraction success on static pages.

## Iteration 0.4: Agentic Validation and Intelligence Outputs

### Goal

Improve usefulness and decision quality.

### Scope

- Planner Agent v1.
- Source Selection Agent v1.
- Quality Critic Agent v1.
- Entity Resolution Agent v1.
- Extraction Validation Agent v1.
- Agent Decision Logger.
- Intelligence Card Generator.
- Evidence Graph v1.
- Summary API.
- Vertical Packs v1.

### Expectations

- Generate structured intelligence cards.
- Use AI for ambiguous entity resolution.
- Use AI for quality criticism only on borderline/high-value results.
- Validate extracted content for CAPTCHA, login pages, soft 404s, boilerplate, and wrong language.
- Log every AI decision.
- Produce evidence-backed summaries.
- Support at least two vertical use cases well.

### Acceptance Criteria

- Agent decisions logged for 100% AI-assisted cases.
- AI cannot bypass crawl policy.
- At least 85% extraction validation accuracy.
- Evidence attached to summaries.
- At least two vertical packs usable end-to-end.

## Iteration 0.5: Scale, Benchmarking, Optimization, and Production Readiness

### Goal

Improve speed, efficiency, reliability, observability, and production readiness.

### Scope

- Benchmark Runner.
- A/B Test Router.
- Latency-Aware Execution Planner.
- Fast / Standard / Deep Query Modes.
- Query Cache.
- Entity Cache.
- Robots Cache.
- Embedding Cache.
- Hybrid Retrieval.
- Reranker.
- Observability Dashboards.
- DLQ Monitoring.
- Admin Review Queue.
- Provider Health Monitoring.
- Optional Paid SERP Adapter.
- Playwright Fallback.
- Deployment Hardening.

### Expectations

- Support production deployment.
- Run benchmark datasets.
- Compare experiments.
- Track quality over time.
- Improve response time using caching.
- Support fast, standard, and deep execution paths.
- Route away from unhealthy providers.
- Use Playwright only as fallback.
- Use paid SERP only when benchmark-justified.

### Acceptance Criteria

- Fast mode response: 1 to 3 seconds for cached/indexed queries.
- Standard mode response: 5 to 20 seconds for source-backed queries.
- At least 30% reduction in unnecessary live crawls.
- At least 25% reduction in repeated source calls through caching.
- A/B test framework operational.
- Provider health dashboard operational.
- DLQ dashboard operational.
- Admin review queue operational.

## Maturity Model

```text
Iteration 0.1: CredenceAI can search.
Iteration 0.2: CredenceAI can decide which results are trustworthy.
Iteration 0.3: CredenceAI can safely collect and extract source content.
Iteration 0.4: CredenceAI can generate intelligence outputs from validated evidence.
Iteration 0.5: CredenceAI can scale, measure itself, optimize performance, and run in production.
```
