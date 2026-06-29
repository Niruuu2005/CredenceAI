# API Specification

## API Principles

- All jobs must have a trace ID.
- All trusted results must include provenance.
- All asynchronous jobs must expose status.
- Output format should support human UI, APIs, and dataset exports.

## Submit Job

```http
POST /jobs
```

### Request

```json
{
  "job_type": "search_query",
  "input": "open source search engines",
  "priority": "normal",
  "routing_mode": "free_first",
  "execution_mode": "standard"
}
```

### Response

```json
{
  "job_id": "job_123",
  "trace_id": "trace_abc",
  "status": "queued",
  "created_at": "2026-06-16T00:00:00Z"
}
```

## Get Job Status

```http
GET /jobs/{job_id}
```

### Response

```json
{
  "job_id": "job_123",
  "status": "completed",
  "results_count": 42,
  "failed_events": 0,
  "quality_summary": {
    "accepted": 30,
    "rejected": 8,
    "manual_review": 4
  }
}
```

## Search Internal Index

```http
GET /search?q=example&mode=standard
```

### Response

```json
{
  "query": "example",
  "mode": "standard",
  "results": [
    {
      "title": "Example Document",
      "url": "https://example.com",
      "quality_score": 0.86,
      "entities": [],
      "source": "searxng",
      "decision": "accept"
    }
  ]
}
```

## Entity Lookup

```http
GET /entities?name=Tesla
```

### Response

```json
{
  "canonical_name": "Tesla Inc.",
  "entity_type": "organization",
  "aliases": ["Tesla Motors"],
  "confidence": 0.94,
  "related_documents": []
}
```

## URL Crawl Request

```http
POST /crawl
```

### Request

```json
{
  "url": "https://example.com/article",
  "crawl_depth": 1,
  "freshness_required": "medium"
}
```

### Response

```json
{
  "crawl_job_id": "crawl_123",
  "policy_decision": "pending",
  "status": "queued"
}
```

## Intelligence Card

```http
GET /intelligence/cards/{entity_id}
```

### Response

```json
{
  "entity_id": "ent_123",
  "name": "Example Company",
  "summary": "...",
  "recent_news": [],
  "risk_signals": [],
  "related_entities": [],
  "source_confidence": 0.84
}
```

## RAG Dataset Export

```http
POST /exports/rag-dataset
```

### Request

```json
{
  "collection_id": "col_123",
  "format": "jsonl",
  "include_embeddings": false,
  "include_citations": true
}
```

### Response

```json
{
  "export_id": "exp_123",
  "status": "queued"
}
```

## Admin Review Queue

```http
GET /review/queue
```

Used for:

- Ambiguous entities.
- Low-confidence documents.
- Policy conflicts.
- Schema failures.
- Source conflicts.
- Borderline trust score results.

## Error Format

```json
{
  "error": {
    "code": "INVALID_JOB_TYPE",
    "message": "Unsupported job_type provided.",
    "details": {},
    "trace_id": "trace_abc"
  }
}
```
