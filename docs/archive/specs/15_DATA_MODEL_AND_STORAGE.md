# Data Model and Storage

## Storage Responsibilities

| Store | Responsibility |
|---|---|
| Postgres | Transactional metadata, jobs, sources, entities, scores, decisions. |
| MinIO/S3 | Raw payloads, HTML, extracted files, binaries, WARC, screenshots. |
| OpenSearch | Search index for trusted documents and results. |
| Redis | Cache, lock, lightweight queue, robots cache, entity cache. |
| Kafka | Durable event streaming. |
| Graph/Entity Store | Entity relationships, aliases, evidence graph. |
| Analytics Store | Benchmark, A/B, cost, latency, operational metrics. |

## Core Tables

### jobs

```sql
id
trace_id
job_type
input
vertical
priority
routing_mode
execution_mode
status
created_at
updated_at
completed_at
error_message
```

### source_results

```sql
id
job_id
source
source_type
input_value
raw_payload_ref
status
confidence
fetched_at
schema_version
```

### normalized_results

```sql
id
job_id
source_result_id
title
url
canonical_url
snippet
source
language
published_at
fetched_at
raw_payload_ref
created_at
```

### quality_scores

```sql
id
result_id
relevance_score
source_reliability_score
freshness_score
authority_score
entity_match_score
dedup_confidence
extraction_likelihood_score
risk_score
final_trust_score
decision
reason
created_at
```

### dedup_groups

```sql
id
group_type
canonical_result_id
canonical_url
content_hash
simhash
created_at
```

### dedup_members

```sql
id
group_id
result_id
match_type
confidence
created_at
```

### entities

```sql
id
canonical_name
entity_type
description
official_url
wikidata_id
wikipedia_url
openalex_id
created_at
updated_at
```

### entity_aliases

```sql
id
entity_id
alias
language
valid_from
valid_to
source
confidence
```

### entity_links

```sql
id
entity_id
result_id
document_id
mention
confidence
decision
created_at
```

### crawl_policy_decisions

```sql
id
url
domain
robots_allowed
rate_limit_ok
private_ip_blocked
content_type_allowed
risk_score
decision
reason
created_at
```

### crawl_jobs

```sql
id
url
canonical_url
crawl_policy_decision_id
crawler_type
status
attempts
started_at
completed_at
error_message
```

### documents

```sql
id
url
canonical_url
title
main_text_ref
html_ref
language
content_hash
readability_score
extraction_quality_score
freshness_score
indexed_at
created_at
```

### evidence_items

```sql
id
claim_id
document_id
source
url
extracted_text_ref
confidence
created_at
```

### claims

```sql
id
entity_id
claim_text
claim_type
claim_confidence
created_at
updated_at
```

### agent_decisions

```sql
id
agent_name
job_id
input_ref
decision
reason
confidence
created_at
```

### ab_experiments

```sql
id
name
description
status
variant_a
variant_b
success_metric
started_at
ended_at
created_at
```

### ab_assignments

```sql
id
experiment_id
job_id
input_hash
variant
assigned_at
```

### source_conflicts

```sql
id
entity_id
document_id
field_name
source_a
value_a
source_b
value_b
resolution_status
created_at
```

## Object Storage Layout

```text
raw/{source}/{yyyy}/{mm}/{dd}/{job_id}.json
raw/html/{domain}/{crawl_job_id}.html
processed/documents/{document_id}/main.txt
processed/documents/{document_id}/metadata.json
processed/media/{media_id}/original.bin
exports/{export_id}/dataset.jsonl
benchmarks/{run_id}/results.json
```

## Index Design

### OpenSearch Indexes

| Index | Content |
|---|---|
| credence-results | Search result metadata. |
| credence-documents | Trusted extracted documents. |
| credence-entities | Canonical entity profiles. |
| credence-intelligence-cards | Generated intelligence cards. |
| credence-evidence | Claims and evidence links. |

## Retention Policy

| Data type | Retention |
|---|---|
| Raw payloads | Configurable, default 90 days. |
| Trusted metadata | Long-term. |
| Audit logs | Long-term or compliance-defined. |
| Failed payloads | 30 to 90 days. |
| Benchmark runs | Long-term for trend analysis. |
| Cache entries | TTL-based. |
