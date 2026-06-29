# Quality Scoring, Deduplication, and Entity Resolution

## Quality Scoring

### Purpose

The Quality Scorer decides whether a result deserves enrichment, crawling, indexing, rejection, or manual review.

### Component Scores

```json
{
  "relevance_score": 0.91,
  "source_reliability_score": 0.83,
  "freshness_score": 0.77,
  "authority_score": 0.79,
  "entity_confidence": 0.88,
  "dedup_confidence": 0.94,
  "extraction_likelihood_score": 0.81,
  "risk_score": 0.12,
  "final_trust_score": 0.84,
  "decision": "index_with_confidence"
}
```

### Decision Thresholds

| Score | Decision |
|---:|---|
| 0.85 to 1.00 | Accept, crawl/index if policy allows. |
| 0.70 to 0.84 | Accept with confidence flag, enrich if useful. |
| 0.55 to 0.69 | Store metadata, low-priority crawl or review. |
| 0.40 to 0.54 | Manual review or enrich more. |
| Below 0.40 | Reject or quarantine. |

### Thresholds by Use Case

| Use case | Minimum trust score | Rationale |
|---|---:|---|
| Brand monitoring | 0.65 | Recall matters. |
| Compliance/risk | 0.85 | Precision matters. |
| RAG dataset | 0.80 | Context quality matters. |
| News monitoring | 0.70 | Freshness matters. |
| Scholarly search | 0.75 | Metadata completeness matters. |

## Deduplication

### Targets

- URLs.
- Documents.
- Media files.
- Entities.
- Scholarly papers.
- News articles.
- Archived pages.
- Search results.

### Stages

```text
Normalize URL
→ remove tracking parameters
→ resolve redirects
→ compare canonical URL
→ compare content hash
→ compare SimHash / MinHash
→ compare title + author + publish date
→ merge duplicate entities/documents
```

### Edge Cases

| Case | Handling |
|---|---|
| Same article syndicated across sites | Keep all sources, choose canonical document. |
| Same URL with UTM parameters | Strip tracking params. |
| HTTP and HTTPS versions | Prefer HTTPS unless content differs. |
| Mobile and desktop pages | Merge if content equivalent. |
| arXiv and journal version | Link as related versions, not exact duplicates. |
| PDF and HTML version | Store both, group under same work. |
| Same image resized | Perceptual hash comparison. |

## Entity Resolution

### Flow

```text
mention detected
→ candidate generation
→ candidate scoring
→ context comparison
→ confidence decision
→ entity link / reject / manual review
```

### Entity Score

```text
entity_score =
  name_similarity
+ alias_match
+ external_id_match
+ context_similarity
+ domain_match
+ location_match
+ type_match
+ source_consistency
- ambiguity_penalty
```

### Decision Policy

| Confidence | Action |
|---:|---|
| 0.95+ | Auto-link. |
| 0.85 to 0.94 | Link with confidence flag. |
| 0.70 to 0.84 | Use in ranking, not canonical. |
| 0.50 to 0.69 | Review or enrich. |
| Below 0.50 | Reject. |

## Source Conflict Handling

Do not overwrite conflicting data. Store conflicts explicitly.

```json
{
  "field": "publication_date",
  "values": [
    {"source": "openalex", "value": "2023", "confidence": 0.72},
    {"source": "crossref", "value": "2024", "confidence": 0.81},
    {"source": "arxiv", "value": "2022-11-04", "confidence": 0.89}
  ],
  "resolved_value": "2022-11-04",
  "resolution_reason": "earliest known preprint version"
}
```

## Accuracy Improvements

- Use labeled evaluation datasets.
- Calibrate score thresholds by vertical.
- Log false positives and false negatives.
- Use benchmark-driven scoring changes.
- Keep confidence components visible instead of hiding everything behind one magic number.
