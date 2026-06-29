# Deployment and Operations

## Environments

| Environment | Purpose |
|---|---|
| local | Developer testing using Docker Compose. |
| dev | Shared integration environment. |
| staging | Production-like test environment. |
| production | Live system with monitoring, backups, security controls. |

## Recommended Runtime Components

- FastAPI services.
- Worker processes for adapters, scoring, dedup, entity resolution, crawling, extraction, indexing.
- Postgres.
- Redis.
- Kafka.
- OpenSearch.
- MinIO/S3.
- Prometheus/Grafana.
- ELK/Loki for logs.
- Docker Compose initially, Kubernetes later.

## Deployment Progression

| Iteration | Deployment style |
|---:|---|
| 1 | Docker Compose local/dev. |
| 2 | Docker Compose with persistent volumes and backups. |
| 3 | Queue-based workers and isolated crawler containers. |
| 4 | Agent services and admin review workflows. |
| 5 | Kubernetes or managed container runtime with scaling and SLOs. |

## Scaling Strategy

Scale independently:

- Source adapter workers.
- Crawl policy workers.
- Static crawler workers.
- Browser crawler workers.
- Extraction workers.
- Entity resolution workers.
- Indexing workers.
- Agent workers.

## Operational Runbooks

### Provider degradation

1. Check provider health dashboard.
2. Confirm error/timeout spike.
3. Reduce source weight.
4. Enable fallback source.
5. Alert admin if degradation continues.

### DLQ growth

1. Identify top error types.
2. Inspect sample failed payloads.
3. Decide retry, patch, quarantine, or ignore.
4. Add regression test for repeated failures.

### Crawl failure spike

1. Check robots block rate.
2. Check domain rate limits.
3. Check crawler CPU/memory.
4. Reduce crawl concurrency.
5. Pause low-priority crawls.

### OpenSearch indexing delay

1. Check indexing queue lag.
2. Check OpenSearch cluster health.
3. Scale indexing workers.
4. Reduce bulk size if needed.
5. Retry failed indexing events.

## Backup Strategy

| System | Backup |
|---|---|
| Postgres | Automated daily snapshot + PITR where possible. |
| MinIO | Versioned buckets and replication if needed. |
| OpenSearch | Snapshot repository. |
| Configuration | Git + secret manager backup. |
| Benchmark results | Long-term archive. |

## Operational SLOs

| Area | Target |
|---|---|
| Job API uptime | 99.5% for MVP, 99.9% later. |
| Fast mode p95 | Under 3 seconds. |
| Standard mode p95 | Under 20 seconds. |
| Job failure visibility | 100% failures visible in DLQ/admin. |
| Raw payload audit | 100% source calls preserve raw refs. |
| Security policy bypass | 0 tolerated. |
