# Strict Researcher Evaluation

## Verdict

CredenceAI is a strong concept because it focuses on the missing middle layer between raw search/crawl data and trusted intelligence. The project has a valuable foundation: source orchestration, normalization, quality scoring, deduplication, entity resolution, safe crawling, extraction, AI validation, indexing, benchmarking, and A/B testing.

The main weakness is scope risk. The system can become too broad if it tries to support every use case, every source, every crawler, every AI agent, and every vertical from day one. That is how software becomes a museum of unfinished components.

## Best Refined Product Thesis

CredenceAI should become a trusted intelligence generation platform:

> A system that transforms messy public data into verified, deduplicated, entity-aware, source-traceable intelligence for humans, APIs, monitoring systems, and AI/RAG pipelines.

## Strengths

| Strength | Why it matters |
|---|---|
| Free-first architecture | Reduces vendor dependency and cost. |
| Modular source adapters | Allows incremental source expansion. |
| Trust before indexing | Prevents noisy and low-quality data from polluting search/RAG systems. |
| Entity resolution | Enables company, person, place, paper, product, and domain intelligence. |
| Safe crawling | Reduces security, legal, and operational risk. |
| Agentic validation | Useful for ambiguous and high-value cases. |
| Benchmarking mindset | Prevents unmeasured architecture drift. |
| Self-hostable direction | Valuable for enterprises, researchers, and open-source communities. |

## Weaknesses

| Weakness | Risk | Fix |
|---|---|---|
| Too many components for MVP | Slow delivery and integration drag | Use a five-iteration scope. |
| Quality score may become decorative math | Inaccurate trust decisions | Calibrate scores using labeled benchmark datasets. |
| AI agents can increase latency and cost | Slow responses and expensive jobs | Use agents only for borderline, ambiguous, or high-value cases. |
| Batch and interactive paths are mixed | Bad user experience | Split Fast, Standard, and Deep execution modes. |
| Broad positioning | Confusing product story | Use vertical intelligence packs. |
| Entity resolution complexity | False merges and wrong profiles | Apply confidence thresholds and manual review. |
| Crawling scope explosion | Cost and compliance risk | Score before crawl and enforce budgets. |

## Recommended Use-Case Expansion Strategy

Do not position CredenceAI as a tool for everyone. Broaden it using vertical intelligence packs.

| Pack | Primary users | Output |
|---|---|---|
| Company Intelligence Pack | Strategy, sales, investors, product teams | Company cards, competitor monitoring, timelines. |
| Research Intelligence Pack | R&D, academia, innovation teams | Paper cards, topic maps, author/institution graphs. |
| News and Narrative Intelligence Pack | PR, media, OSINT, policy teams | Event timelines, source clusters, narrative maps. |
| RAG Dataset Builder Pack | AI/data teams | Clean chunks, citations, embeddings, metadata. |
| Risk and Compliance Pack | Compliance, vendor risk, security teams | Risk cards, evidence bundles, audit trails. |

## Accuracy Improvements

1. Use claim-level evidence objects.
2. Split final trust score into component scores.
3. Use hybrid retrieval: BM25 + vector + metadata + entity filters + reranking.
4. Add source reliability profiles per vertical.
5. Track source conflicts explicitly instead of overwriting data.
6. Calibrate entity confidence thresholds.
7. Use benchmark datasets before accepting scoring changes.

## Efficiency Improvements

1. Use source cascades instead of source blasting.
2. Cache query, entity, URL canonicalization, robots.txt, extraction, and embedding results.
3. Use Common Crawl before live crawling when freshness does not matter.
4. Make Playwright rare and budget-controlled.
5. Add per-job budgets for sources, crawls, browser pages, LLM calls, and deadlines.

## Response-Time Improvements

Use three execution modes:

| Mode | Target response time | Behavior |
|---|---:|---|
| Fast | 1 to 3 seconds | Cache/index/entity card only. |
| Standard | 5 to 20 seconds | Source search + light validation + no browser crawl. |
| Deep | Longer job | Full crawl, extraction, entity resolution, evidence synthesis. |

## Recommended MVP Narrowing

For Iteration 0.1 and Iteration 0.2, focus on:

- Search query.
- Entity lookup.
- News monitoring light mode.
- Research collection light mode.
- Company intelligence starter pack.

Delay:

- Nutch.
- Heritrix.
- Advanced media intelligence.
- Full autonomous agent mesh.
- Paid SERP adapters.
- Complex admin UI.

## Final Researcher Recommendation

Build CredenceAI around five pillars:

1. Source intelligence.
2. Evidence and provenance.
3. Quality and entity resolution.
4. Safe selective crawling.
5. Benchmark-driven optimization.

The final product should be judged by measurable improvements in accuracy, deduplication, freshness, latency, source-call efficiency, crawl reduction, evidence coverage, and user acceptance.
