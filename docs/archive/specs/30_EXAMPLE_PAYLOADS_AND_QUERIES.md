# Example Payloads and Queries

## Search Query

```json
{
  "job_type": "search_query",
  "input": "best open source metasearch engines",
  "routing_mode": "free_first",
  "execution_mode": "standard"
}
```

## Entity Lookup

```json
{
  "job_type": "entity_lookup",
  "input": "Apple",
  "vertical": "company_intelligence",
  "requires_entity_resolution": true
}
```

Expected behavior:

- Generate candidates: Apple Inc., apple fruit, Apple Records.
- Use context and source evidence.
- Return canonical entity with confidence.

## Competitor Monitoring

```json
{
  "job_type": "competitor_monitoring",
  "input": "Perplexity AI",
  "vertical": "company_intelligence",
  "freshness_required": "high",
  "output_mode": "intelligence_card"
}
```

Expected output:

- Company card.
- Recent news.
- Product updates.
- Related entities.
- Risk/opportunity signals.
- Source confidence.

## Research Collection

```json
{
  "job_type": "research_collection",
  "input": "agentic search intelligence systems",
  "vertical": "research",
  "sources": ["openalex", "crossref", "arxiv", "searxng"],
  "output_format": "collection"
}
```

Expected output:

- Paper list.
- Author/institution graph.
- Metadata conflict report.
- Topic summary.
- Exportable collection.

## RAG Dataset Builder

```json
{
  "job_type": "rag_dataset_builder",
  "input": "enterprise AI search architecture",
  "execution_mode": "deep",
  "include_citations": true,
  "include_entity_links": true,
  "output_format": "jsonl"
}
```

Expected output:

```json
{
  "chunks": [],
  "metadata": {},
  "citations": [],
  "entity_links": [],
  "quality_scores": {},
  "embedding_ready": true
}
```

## Risk Monitoring

```json
{
  "job_type": "risk_monitoring",
  "input": "Example Vendor data breach regulatory notice",
  "vertical": "risk_compliance",
  "minimum_trust_score": 0.85,
  "freshness_required": "high"
}
```

Expected output:

- Alert severity.
- Evidence URLs.
- Official source preference.
- Source confidence.
- Review requirement if confidence is low.

## URL Crawl

```json
{
  "job_type": "url_crawl",
  "input": "https://example.com/article",
  "crawl_depth": 1,
  "freshness_required": "medium",
  "enable_extraction": true
}
```

Expected output:

- Crawl policy decision.
- Extracted text.
- Metadata.
- Content hash.
- Extraction quality score.
- Indexing decision.

## Intelligence Card Request

```json
{
  "job_type": "intelligence_card_request",
  "input": "Tesla Inc.",
  "vertical": "company_intelligence",
  "sections": [
    "canonical_profile",
    "recent_news",
    "related_entities",
    "risk_signals",
    "timeline"
  ]
}
```

Expected output:

- Entity profile.
- Official website.
- Aliases.
- News.
- Related entities.
- Evidence-backed summary.
- Confidence and provenance.
