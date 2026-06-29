# Definition, USP, and Positioning

## Definition

CredenceAI is a free-first, open-source, AI-assisted search intelligence platform that converts noisy public web, news, research, archive, and entity data into verified, deduplicated, source-traceable, searchable intelligence.

It is not only a search engine, crawler, vector database, RAG tool, or AI summarizer. It is an intelligence refinery.

```text
Raw search results / web data
→ source routing
→ normalization
→ quality scoring
→ deduplication
→ entity resolution
→ safe crawling
→ extraction
→ AI-assisted validation
→ trusted searchable intelligence
```

## One-Line Positioning

CredenceAI is a trusted intelligence layer that converts noisy web and open-source data into verified, evidence-backed knowledge for analysts, enterprises, researchers, and AI systems.

## Primary USP

CredenceAI owns the full trust pipeline from discovery to validated indexing while remaining free-first and open-source by default.

Most tools solve only one layer:

| Tool type | What it usually does | Limitation |
|---|---|---|
| SERP API | Returns search results | Not trust-aware, can become costly. |
| Crawler | Collects pages | Needs policy, scoring, extraction, and validation around it. |
| Search index | Retrieves stored data | Requires clean data first. |
| Vector database | Retrieves semantic chunks | Can retrieve low-quality or stale content. |
| AI search agent | Searches and summarizes | Often less auditable and less governed. |
| Scholarly API | Provides research metadata | Usually source-specific and not unified with web/news/archive data. |

CredenceAI combines these into a governed trust pipeline:

```text
Discover → Verify → Score → Deduplicate → Resolve Entities → Crawl Safely → Validate → Index → Benchmark
```

## Key USPs

### 1. Free-first source strategy

CredenceAI uses open and free sources first:

- SearXNG.
- Wikidata.
- Wikipedia.
- Common Crawl.
- GDELT.
- OpenAlex.
- Crossref.
- arXiv.
- Internet Archive.
- OpenStreetMap / Nominatim.

Paid SERP APIs are optional fallback tools, not the foundation.

### 2. Trust before indexing

CredenceAI does not blindly index everything it finds. Results must pass quality, deduplication, entity, crawl-policy, extraction, and validation gates before becoming trusted searchable intelligence.

### 3. Evidence-backed intelligence

Each result should preserve:

- Source.
- URL.
- Raw payload reference.
- Crawl timestamp.
- Quality score.
- Entity confidence.
- Extraction score.
- Decision reason.
- Audit trail.

### 4. Entity-aware intelligence

CredenceAI resolves ambiguous names into canonical entities.

Examples:

| Mention | Possible meanings | Resolution signals |
|---|---|---|
| Apple | Apple Inc., apple fruit, Apple Records | Context, type, aliases, official domain. |
| Tesla | Tesla Inc., Nikola Tesla, tesla unit | Co-mentioned terms, entity type, date, source. |
| OpenAI | Company, research papers, products | Context, source, official IDs. |

### 5. Safe selective crawling

CredenceAI checks robots.txt, rate limits, private IP redirects, MIME type, file size, malware risk, source terms, and crawl budget before crawling.

### 6. Governed agentic AI

AI agents assist with planning, source selection, quality critique, entity ambiguity, extraction validation, summaries, experiment recommendations, and operations. They must not bypass deterministic safety gates.

### 7. Benchmark-driven improvement

Every improvement must prove value through metrics such as precision, duplicate rate, freshness, extraction success, latency, cost, and user acceptance.

### 8. RAG-ready outputs

CredenceAI can produce clean, citation-rich, source-traceable, chunked documents for AI/RAG systems.

## Target Positioning Statement

CredenceAI is a free-first, self-hostable intelligence refinery that transforms noisy search, crawl, news, archive, research, and entity data into verified, deduplicated, evidence-backed knowledge for search, monitoring, analytics, and AI/RAG systems.
