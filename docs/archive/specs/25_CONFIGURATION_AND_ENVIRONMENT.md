# Configuration and Environment

## Configuration Principles

- Use environment variables for deployment-specific configuration.
- Use feature flags for optional sources and experimental modules.
- Keep secrets out of logs and repository.
- Make budgets configurable per job type and tenant.

## Core Environment Variables

```env
APP_ENV=local
APP_NAME=credenceai
DATABASE_URL=postgresql://user:pass@postgres:5432/credenceai
REDIS_URL=redis://redis:6379/0
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=change-me
MINIO_SECRET_KEY=change-me
OPENSEARCH_URL=http://opensearch:9200
LOG_LEVEL=INFO
```

## Source Configuration

```env
SEARXNG_BASE_URL=http://searxng:8080
ENABLE_WIKIDATA=true
ENABLE_WIKIPEDIA=true
ENABLE_GDELT=true
ENABLE_COMMONCRAWL=true
ENABLE_OPENALEX=true
ENABLE_CROSSREF=false
ENABLE_ARXIV=false
ENABLE_PAID_SERP=false
```

## Crawler Configuration

```env
CRAWL_USER_AGENT=CredenceAI-Bot/0.1
CRAWL_MAX_DEPTH=1
CRAWL_MAX_FILE_SIZE_MB=20
CRAWL_DOMAIN_RATE_LIMIT_PER_MINUTE=30
ENABLE_PLAYWRIGHT=false
PLAYWRIGHT_MAX_PAGES_PER_JOB=3
PLAYWRIGHT_TIMEOUT_MS=20000
```

## AI Agent Configuration

```env
ENABLE_AGENT_PLANNER=false
ENABLE_AGENT_QUALITY_CRITIC=false
ENABLE_AGENT_ENTITY_RESOLUTION=false
MAX_LLM_CALLS_PER_JOB=5
AI_VALIDATION_MIN_SCORE=0.55
AI_VALIDATION_MAX_SCORE=0.85
```

## Budget Configuration

```env
DEFAULT_MAX_SOURCES=4
DEFAULT_MAX_URLS_TO_CRAWL=20
DEFAULT_MAX_BROWSER_PAGES=3
DEFAULT_DEADLINE_MS=12000
DEFAULT_MINIMUM_CONFIDENCE=0.75
```

## Feature Flags

| Flag | Purpose |
|---|---|
| ENABLE_PLAYWRIGHT | Enable restricted JS fallback crawling. |
| ENABLE_PAID_SERP | Enable optional paid SERP providers. |
| ENABLE_AGENT_QUALITY_CRITIC | Use AI for borderline quality cases. |
| ENABLE_EVIDENCE_GRAPH | Build claim/evidence graph. |
| ENABLE_VECTOR_INDEXING | Generate/store embeddings. |
| ENABLE_AB_TESTING | Assign jobs to experiments. |
| ENABLE_RAG_EXPORT | Enable RAG dataset exports. |

## Secrets Management

For production:

- Use a secret manager.
- Rotate provider API keys.
- Redact secrets from logs.
- Avoid storing secrets in job payloads.
- Audit secret access.

## Configuration Validation

At startup, services must validate:

- Required environment variables.
- Source enabled/disabled state.
- Storage connectivity.
- Queue connectivity.
- Index connectivity.
- Security defaults.
