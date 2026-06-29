# End-to-End Workflows

## Workflow 1: General Search Query

```text
User submits search query
→ Job API validates payload
→ Intent Classifier identifies search_query
→ Source Orchestrator selects SearXNG and optional open sources
→ Adapters return raw payloads
→ Raw payloads stored in MinIO
→ Source Normalizer maps results to common schema
→ Quality Scorer assigns trust components
→ Dedup Worker groups duplicates
→ Entity Resolver links detected entities
→ Trusted results indexed in OpenSearch
→ Result API returns ranked results
```

## Workflow 2: Entity Lookup

```text
Input entity mention
→ Generate entity candidates
→ Search Wikidata/Wikipedia/internal entity store
→ Compare aliases, type, context, official domains, source evidence
→ Score candidates
→ Return canonical entity, aliases, confidence, related documents
```

## Workflow 3: News Monitoring

```text
Scheduler triggers monitoring job
→ Intent Classifier detects news/event monitoring
→ Source Orchestrator selects GDELT + SearXNG news
→ Results normalized
→ Freshness and source reliability scored
→ Duplicates grouped
→ Entities linked
→ Risk/importance signals calculated
→ Alerts emitted only for meaningful new items
```

## Workflow 4: Safe URL Crawl

```text
URL candidate selected
→ Quality score and dedup check
→ Crawl Policy Service checks robots, rate limits, SSRF, MIME, file size
→ Crawl Scheduler prioritizes
→ Scrapy crawls static page
→ Playwright used only if static extraction fails and page value is high
→ Extract title, main text, metadata, links, language, hashes
→ Validate extraction quality
→ Index trusted extracted document
```

## Workflow 5: Research Collection

```text
Research topic submitted
→ Planner decomposes into searches/entities/scholarly lookups
→ Source Orchestrator queries OpenAlex, Crossref, arXiv, SearXNG
→ Metadata normalized
→ Duplicate papers grouped
→ Authors and institutions resolved
→ Source conflicts stored
→ Papers and evidence indexed
→ Research collection exported
```

## Workflow 6: RAG Dataset Builder

```text
Dataset request submitted
→ Sources selected by vertical and trust policy
→ Documents discovered and scored
→ Crawl/extract only approved high-value sources
→ Deduplicate and entity-link documents
→ Chunk extracted content
→ Attach citations, metadata, quality scores, freshness scores
→ Export JSONL/Parquet/OpenSearch index payload
```

## Workflow 7: Intelligence Card Generation

```text
Entity request submitted
→ Resolve canonical entity
→ Gather official sources, news, research, archives, mentions
→ Score and deduplicate evidence
→ Build evidence graph
→ Generate structured card sections
→ Validate summary against evidence
→ Return card with confidence and provenance
```

## Workflow 8: A/B Experiment

```text
Experiment configured
→ Jobs assigned to variant A or B
→ Same input set processed through variant pipelines
→ Metrics captured: precision, duplicate rate, latency, cost, extraction success
→ Statistical comparison performed
→ Winner recommended or experiment rejected
```

## Workflow 9: Provider Degradation

```text
Provider timeout/error rate rises
→ Provider health monitor detects degradation
→ Source Orchestrator reduces provider weight
→ Fallback provider selected
→ Ops alert emitted
→ Provider recovers or remains downgraded
```
