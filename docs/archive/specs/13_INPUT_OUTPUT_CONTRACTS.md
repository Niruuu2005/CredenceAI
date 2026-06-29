# Input and Output Contracts

## Job Request

```json
{
  "job_type": "search_query",
  "input": "open source search engines",
  "vertical": "web",
  "priority": "normal",
  "routing_mode": "free_first",
  "freshness_required": "medium",
  "crawl_depth": 1,
  "execution_mode": "standard",
  "enable_ai_validation": true,
  "max_sources": 4,
  "max_urls_to_crawl": 20,
  "max_llm_calls": 5,
  "deadline_ms": 12000
}
```

## Intent Output

```json
{
  "intent": "scholarly_search",
  "entities": ["OpenAI"],
  "vertical": "research",
  "requires_freshness": true,
  "requires_crawling": true,
  "requires_entity_resolution": true,
  "risk_level": "low",
  "language": "en"
}
```

## Source Adapter Output

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

## Normalized Result

```json
{
  "result_id": "res_123",
  "job_id": "job_123",
  "title": "Example Document",
  "url": "https://example.com/page",
  "canonical_url": "https://example.com/page",
  "snippet": "...",
  "source": "searxng",
  "source_type": "web",
  "published_at": null,
  "fetched_at": "2026-06-16T00:00:00Z",
  "language": "en",
  "raw_payload_ref": "s3://raw/searxng/job_123.json"
}
```

## Quality Score Output

```json
{
  "result_id": "res_123",
  "relevance_score": 0.91,
  "source_reliability_score": 0.83,
  "freshness_score": 0.77,
  "entity_confidence": 0.88,
  "dedup_confidence": 0.94,
  "extraction_likelihood_score": 0.81,
  "risk_score": 0.12,
  "final_trust_score": 0.84,
  "decision": "index_with_confidence",
  "reason": "High relevance, reliable source, fresh enough, low risk."
}
```

## Entity Resolution Output

```json
{
  "mention": "Apple",
  "canonical_entity_id": "ent_apple_inc",
  "canonical_name": "Apple Inc.",
  "entity_type": "organization",
  "confidence": 0.93,
  "evidence": [
    "Context includes iPhone and Cupertino",
    "Official website match",
    "Wikidata candidate score high"
  ],
  "decision": "auto_link"
}
```

## Crawl Policy Output

```json
{
  "url": "https://example.com/page",
  "robots_allowed": true,
  "rate_limit_ok": true,
  "private_ip_blocked": false,
  "content_type_allowed": true,
  "risk_score": 0.09,
  "decision": "allowed",
  "crawler_type": "scrapy",
  "reason": "Robots allowed, public IP, safe content type."
}
```

## Extraction Output

```json
{
  "document_id": "doc_123",
  "url": "https://example.com/page",
  "title": "Example Document",
  "main_text_ref": "s3://processed/doc_123/main.txt",
  "main_text_length": 10240,
  "language": "en",
  "content_hash": "sha256:abc123",
  "readability_score": 0.72,
  "extraction_quality_score": 0.86,
  "entities": [],
  "links": [],
  "media_urls": []
}
```

## Evidence Object

```json
{
  "claim": "Company X launched Product Y",
  "evidence": [
    {
      "source": "official_site",
      "url": "https://company.example/product-y",
      "published_at": "2026-06-01",
      "extracted_text_ref": "s3://processed/doc_456/main.txt",
      "confidence": 0.92
    },
    {
      "source": "news",
      "url": "https://news.example/story",
      "confidence": 0.78
    }
  ],
  "claim_confidence": 0.86
}
```

## Intelligence Card Output

```json
{
  "entity": {
    "id": "ent_123",
    "name": "Tesla Inc.",
    "type": "organization",
    "confidence": 0.94
  },
  "sections": {
    "canonical_profile": {},
    "official_sources": [],
    "recent_news": [],
    "research_mentions": [],
    "risk_signals": [],
    "related_entities": [],
    "timeline": []
  },
  "source_confidence": 0.84,
  "generated_at": "2026-06-16T00:00:00Z"
}
```
