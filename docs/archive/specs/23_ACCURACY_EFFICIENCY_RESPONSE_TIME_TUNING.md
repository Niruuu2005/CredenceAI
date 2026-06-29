# Accuracy, Efficiency, and Response-Time Tuning

## Goal

Tune CredenceAI so it improves accuracy, reduces cost, lowers latency, and returns the right output for the right use case.

## Accuracy Tuning

### Evidence-first retrieval

Every final answer or indexed claim should tie back to evidence.

```json
{
  "claim": "Company X launched Product Y",
  "evidence": [
    {
      "source": "official_site",
      "url": "https://example.com/product-y",
      "confidence": 0.92
    }
  ],
  "claim_confidence": 0.86
}
```

### Hybrid retrieval

Use:

```text
BM25 keyword retrieval
+ vector retrieval
+ metadata filters
+ entity filters
+ freshness filters
+ reranking
```

Recommended ranking formula:

```text
final_rank =
0.30 * BM25_score
+ 0.25 * vector_similarity
+ 0.15 * source_reliability
+ 0.10 * freshness
+ 0.10 * entity_match
+ 0.05 * extraction_quality
+ 0.05 * user_intent_fit
```

Tune weights by vertical.

### Better entity resolution

```text
mention
→ candidate generation
→ alias matching
→ context embedding comparison
→ domain/official URL check
→ external ID match
→ confidence calibration
→ link / reject / review
```

### Source reliability profiles

```json
{
  "source": "gdelt",
  "vertical": "news_monitoring",
  "coverage_score": 0.91,
  "freshness_score": 0.92,
  "metadata_accuracy": 0.74,
  "duplicate_risk": 0.58,
  "recommended_use": "event discovery, not final verification"
}
```

## Efficiency Tuning

### Use source cascade, not source blasting

Example company lookup:

```text
Wikidata/Wikipedia first
→ official website
→ SearXNG
→ GDELT
→ crawl only high-confidence pages
```

Example scholarly lookup:

```text
OpenAlex
→ Crossref
→ arXiv
→ SearXNG only if metadata missing
```

Example news monitoring:

```text
GDELT
→ SearXNG news
→ official/regulatory pages
→ crawl top ranked URLs
```

### Cache hierarchy

| Cache | Purpose | Suggested TTL |
|---|---|---:|
| Query result cache | Avoid repeated source calls | 5 min to 24 hr by vertical |
| URL canonical cache | Avoid repeated normalization | 7 days |
| Robots.txt cache | Avoid repeated robots lookups | 24 hours |
| Entity candidate cache | Speed up entity linking | 7 days |
| Extraction cache | Avoid recrawling unchanged pages | content-hash based |
| Embedding cache | Avoid regenerating vectors | content-hash based |
| Source health cache | Route away from failing providers | minutes |

### Common Crawl first policy

```text
If freshness_required = low:
    check Common Crawl first
If page unchanged recently:
    use cached/archive copy
If freshness_required = high:
    live crawl only top-ranked URLs
```

### Budget-aware routing

```json
{
  "max_sources": 4,
  "max_urls_to_crawl": 20,
  "max_browser_pages": 3,
  "max_llm_calls": 5,
  "deadline_ms": 12000,
  "minimum_confidence": 0.75
}
```

## Response-Time Tuning

### Execution modes

| Mode | Target response time | Behavior |
|---|---:|---|
| Fast | 1 to 3 seconds | Index/cache/entity card only. |
| Standard | 5 to 20 seconds | Source search + light validation + no browser crawl. |
| Deep | Longer job | Full crawl, extraction, entity resolution, evidence synthesis. |

### Progressive response model

```text
Stage 1: cached/index result
Stage 2: fresh source results
Stage 3: validated/crawled results
Stage 4: final evidence-backed synthesis
```

### Precomputed entity cards

For important entities, precompute:

- Canonical profile.
- Aliases.
- Official website.
- Known sources.
- Recent news.
- Risk signals.
- Scholarly links.
- Related entities.

## Output by User Type

| User type | Output |
|---|---|
| Analyst | Summary, key findings, evidence table, confidence, source links. |
| API user | JSON response with entities, documents, evidence, warnings. |
| RAG system | Chunks, metadata, citations, entity links, quality scores. |
| Monitoring user | Alert, severity, change description, evidence, recommended action. |

## Tuning Success Metrics

- top_10_precision.
- entity_resolution_accuracy.
- duplicate_rate.
- evidence_coverage.
- p50/p95 response time.
- source calls per query.
- crawl avoidance rate.
- LLM calls per job.
- cost per query.
