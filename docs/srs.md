Functional contracts, data design, quality attributes and verification criteria for CredenceAI 2.0.

| Project | CredenceAI 2.0                                        |
|---------|-------------------------------------------------------|
| Status  | Proposed requirements; subject to review and approval |
| Basis   | CredenceAI project definition v2.0, 14 October 2026   |

# 1. Introduction

Purpose: specify implementable and verifiable v2 requirements for an evidence-first research platform. Scope: modular FastAPI monolith, independent durable workers, React client, TypeScript SDK, PostgreSQL, reconstructable indexes and rights-aware object storage. Existing v1 routes/data must remain supported through compatible migrations.

Requirement convention: FR = functional, NFR = non-functional, DATA = persistence, API = interface. “Shall” denotes proposed mandatory behavior. All v2 requirements are targets unless explicitly identified as existing MVP capabilities.

# 2. System context and actors

| Actor                   | Interaction                                                        |
|-------------------------|--------------------------------------------------------------------|
| Researcher              | Creates and inspects runs, evidence and reports                    |
| Reviewer                | Annotates relationships and confirms disputed/high-impact findings |
| Workspace administrator | Manages access, quotas and source policy                           |
| Public-source adapter   | Provides metadata or rights-eligible text                          |
| Scheduler / worker      | Executes durable stages and monitors                               |
| SDK client              | Consumes authenticated versioned endpoints                         |

# 3. Functional requirements

## FR-001 Workspace security

All private read/write/search/export/cache access shall use server-derived tenant/workspace authorization context.

**Verification:** Unauthorized cross-workspace requests cannot retrieve resource content.

## FR-002 Research submission

Accept question/claim, workspace, mode, optional language/geography/time/source-class filters, budget and idempotency key.

**Verification:** Valid request creates one identifiable durable run; same idempotency key does not duplicate.

## FR-003 Run lifecycle

Maintain created, queued, planning, retrieving, extracting, normalizing, verifying, reporting and terminal states completed/partial/failed/cancelled/timed_out.

**Verification:** API exposes legal transitions, timestamps, steps and typed failures.

## FR-004 Source routing

Select only enabled, executable, compatible adapters subject to health, policy, language, quotas and budget.

**Verification:** Executed calls match adapter registry; skipped/failed sources show reasons.

## FR-005 Bounded retrieval

Run eligible adapter requests with deadlines, parallelism limits, retries and coverage metadata.

**Verification:** Provider timeout produces recorded failure/partial coverage, not silent success.

## FR-006 Acquisition policy

Fetch only allowed HTTP(S) targets with destination/redirect validation, robots, terms, rate and size checks.

**Verification:** Blocked destinations and retention violations are rejected in security tests.

## FR-007 Provenance

Store canonical/original URLs, publisher, adapter, fetch time, publication time, rights and content/extraction versions where available.

**Verification:** Evidence inspector resolves provenance and separates fetched versus published date.

## FR-008 Snapshots and passages

Create immutable snapshot identifiers with permitted excerpts/content and passage offsets/anchors/hashes.

**Verification:** Passage references re-open the exact authorized evidence version.

## FR-009 Claims

Represent atomic proposition, origin, entity, population, units, geography, time, conditions and extractor version.

**Verification:** Claim scope is preserved and user claims distinguished from extracted claims.

## FR-010 Evidence relationships

Store supports/contradicts/mentions/irrelevant/uncertain per claim-passage pair with reasoning, version and review state.

**Verification:** Every relation resolves to existing claim and authorized passage records.

## FR-011 Source independence

Identify original, secondary, syndicated and common-upstream items for grouping.

**Verification:** Repeated syndicated items do not inflate independent corroboration count.

## FR-012 Verdicts

Produce run-scoped supported/disputed/insufficient_evidence/not_assessed labels; avoid truth probability claims.

**Verification:** Conflicting material evidence yields disputed or escalates for review; missing evidence never implies false.

## FR-013 Evidence inspection

Show claim, highlighted passage, source metadata, independence group, limitations and reviewer notes.

**Verification:** Researcher can navigate from finding to frozen passage.

## FR-014 Human review

Record reviewer identity, timestamp, decision and rationale without rewriting source snapshots.

**Verification:** Review audit trail survives revisions.

## FR-015 Report generation

Build versioned briefs from evidence references and validate every material statement citation.

**Verification:** Unsupported statements are blocked/revised; all final citations resolve.

## FR-016 Report export

Export frozen reports with evidence manifest, coverage warnings, evaluation/config versions and accessible citations.

**Verification:** Export reopens source evidence with permissions preserved.

## FR-017 Collections and monitors

Save evidence in collections, schedule bounded reruns and show added/removed/changed evidence.

**Verification:** Monitor delta corresponds to two recorded versions.

## FR-018 Observability

Record run/stage duration, provider outcome, budget use, error, trace and minimal audit activity.

**Verification:** Telemetry correlates API to worker to report without plaintext secrets.

## FR-019 Backward compatibility

Keep v1 endpoints and historical jobs/data operational through additive migrations/adapters.

**Verification:** Regression suite passes for retained v1 consumers.

# 4. External interfaces and APIs

Frontend: React + Vite + TypeScript + Tailwind research workspace. Backend: FastAPI + Pydantic REST interface. SDK: typed TypeScript client supporting asynchronous runs, evidence models, reviews and monitor deltas. Initial progress updates may use polling; server-sent events are optional.

### 4.1 Research Studio v2 Endpoints

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | `/api/v2/research-runs` | JWT / Key / Guest | Create research run (with guest fallback) |
| GET | `/api/v2/research-runs` | JWT / Key / Guest | List workspace research runs |
| GET | `/api/v2/research-runs/{run_id}` | JWT / Key / Guest | Run status, stages & step duration |
| POST | `/api/v2/research-runs/{run_id}/execute` | JWT / Key / Guest | Execute / resume pipeline stages |
| POST | `/api/v2/research-runs/{run_id}/cancel` | JWT / Key / Guest | Cancel run at next checkpoint |
| GET | `/api/v2/research-runs/{run_id}/sources` | JWT / Key / Guest | Retrieved sources and coverage |
| GET | `/api/v2/research-runs/{run_id}/claims` | JWT / Key / Guest | Scoped claims & calibrated verdicts |
| GET | `/api/v2/research-runs/{run_id}/claims/{claim_id}/evidence` | JWT / Key / Guest | Passage relations & excerpts |
| POST | `/api/v2/research-runs/{run_id}/claims/{claim_id}/evidence/{evidence_id}/review` | JWT / Key / Guest | Reviewer evidence annotation |
| GET | `/api/v2/research-runs/{run_id}/reports/{version}` | JWT / Key / Guest | Frozen citation-validated report |
| POST | `/api/v2/research-runs/{run_id}/reports/{report_id}/approve` | JWT / Key / Guest | Approve report for publication |
| POST | `/api/v2/monitors` | JWT / Key | Create scheduled monitor |
| GET | `/api/v2/monitors/{monitor_id}/deltas` | JWT / Key | Compare scheduled reruns |

### 4.2 Core Platform & Utility Endpoints

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| GET | `/api/health` | None | Service liveness and dependency status |
| POST | `/api/jobs` | JWT / Key | Submit search or crawler job |
| GET | `/api/jobs/{id}` | JWT / Key | Job status and result summary |
| GET | `/api/search` | JWT / Key | Hybrid multi-source search |
| POST | `/api/goals` | JWT / Key | Decompose goal into execution jobs |
| GET / POST | `/api/auth/keys` | JWT | List and generate API keys |
| DELETE | `/api/auth/keys/{id}` | JWT | Revoke an API key |
| GET | `/api/auth/me` | JWT | User profile, quotas, and tier |
| POST | `/api/billing/checkout-session` | JWT | Stripe subscription checkout |
| POST | `/api/billing/webhook` | Stripe Sig | Idempotent billing event handling |

### 4.3 Standard Error Envelope

All API errors return a uniform, machine-readable envelope with correlation tracing:

```json
{
  "error": "validation_error",
  "message": "Human-readable explanation of error condition",
  "trace_id": "trace_9f83a21b4e01",
  "details": []
}
```

HTTP Status Codes: `200` OK, `201` Created, `202` Accepted, `400` Bad Request, `401` Unauthorized, `403` Forbidden, `404` Not Found, `422` Unprocessable Entity, `429` Rate Limit Exceeded, `500` Internal Server Error, `503` Service Unavailable.

# 5. Data requirements & relational schema

PostgreSQL is canonical system of record; full-text and vector indexes are rebuildable projections.

### 5.1 Relational Schema Architecture

- **`tenants`** (`id` PK VARCHAR(50), `name`, `created_at`): Root isolation boundary.
- **`workspaces`** (`id` PK VARCHAR(50), `tenant_id` FK, `name`, `created_at`): Scoped collaboration group.
- **`users`** (`id` PK VARCHAR(50), `email` UNIQUE, `name`, `role`, `account_status`, `plan`): Identity record.
- **`memberships`** (`id` PK, `user_id` FK, `workspace_id` FK, `role`): RBAC membership (`admin`, `editor`, `member`).
- **`api_keys`** (`id` PK, `key_hash` VARCHAR(64) UNIQUE, `owner`, `user_id` FK, `workspace_id` FK, `revoked`): Scoped credentials (`cred_sk_...`).
- **`research_runs`** (`id` PK VARCHAR(50), `workspace_id` FK, `question` TEXT, `mode`, `status`, `config_version`, `created_at`, `completed_at`): Root research lifecycle.
- **`run_steps`** (`id` PK, `run_id` FK, `step_key`, `state`, `attempt_count`, `duration_ms`, `error_message`, `started_at`, `completed_at`): Granular stage execution.
- **`claims`** (`id` PK, `run_id` FK, `proposition` TEXT, `temporal_scope`, `units`, `origin_type`, `verdict`, `rationale`): Atomic propositions.
- **`evidence_edges`** (`id` PK, `claim_id` FK, `passage_id`, `relation`, `rationale`, `passage_text` TEXT, `reviewer_id`, `reviewer_notes`): Grounding connections.
- **`reports`** (`id` PK, `run_id` FK, `title`, `body_markdown` TEXT, `manifest_hash`, `status`, `reviewed_by`): Cryptographically frozen outputs.
- **`monitors`** (`id` PK, `workspace_id` FK, `topic`, `scope`, `status`, `interval`, `last_check`, `health`): Scheduled tracking feeds.
- **`collections`** (`id` PK, `workspace_id` FK, `name`, `description`, `items_count`): Curated research dossiers.

# 6. Processing and reliability requirements

- NFR-001: Persist run creation and transactional outbox event atomically before queue publication.

- NFR-002: Treat queue delivery as at least once; use idempotency key (run_id, step_key, input_version) for each handler.

- NFR-003: Use worker leases, bounded retries with backoff/jitter, cancellation checkpoints and stalled-task recovery.

- NFR-004: Enforce hard per-run limits for provider calls, sources, pages, bytes, duration and AI token/cost budgets.

- NFR-005: Preserve partial-result diagnostics when providers fail; report shall show coverage omissions.

- NFR-006: Cache keys include query/filter signature, access scope, source configuration, evaluator version and freshness window; recheck permissions on hits.

# 7. Security, privacy, legal and model safety

- NFR-007: Require authentication and role/tenant authorization on API, DB queries, search indexes, caches, objects and exports.

- NFR-008: Hash, scope, rotate and revoke API keys; do not reveal keys after issuance. Encrypt transit and storage.

- NFR-009: Prevent SSRF using DNS resolution validation, connect-time destination checks, redirect rechecks and blocklists for loopback/private/link-local/metadata networks.

- NFR-010: Honor provider terms, robots, domain rate limits, content type/byte limits and source retention permissions.

- NFR-011: Treat retrieved pages as untrusted input; use strict schemas and minimally privileged extractors and model tools.

- NFR-012: Record model/rule versions without unnecessary sensitive content in telemetry; escalate contested high-impact results for human review.

- NFR-013: Implement documented retention, deletion, sharing and backup lifecycle.

# 8. Usability and product behavior

- NFR-014: Display real job progress, coverage, failures and cancellation status.

- NFR-015: Do not label search ranking or heuristic source scores as calibrated factual probability.

- NFR-016: Show clear insufficient-evidence/not-assessed outcomes without implying a claim is false.

- NFR-017: Provide evidence inspector, findings board, source explorer, report workspace and monitor/collection views.

- NFR-018: Preserve source and review context for accessible investigation and export; do not silently change historical reports.

# 9. Performance and quality verification

| Area                       | Proposed test / gate                                                                            |
|----------------------------|-------------------------------------------------------------------------------------------------|
| Security                   | Zero known unauthorized cross-tenant retrieval in adversarial paths                             |
| Citation integrity         | 100% report citations resolve to frozen authorized passage IDs                                  |
| Human attribution accuracy | At least 95% of cited material statements supported in held-out review                          |
| Unsupported claims         | At most 5% in initial human-reviewed generated reports                                          |
| Classification             | Publish per-relation precision/recall and confusion matrix                                      |
| Reproducibility            | Frozen input, rule and model versions yield explainable stable outputs or logged nondeterminism |
| Reliability                | Track complete/partial/failure shares, queue age and stage p50/p95                              |
| Resources                  | Verify enforced budgets and cost per run against documented tolerance                           |

Evaluate on a proposed 100–200-question human-labeled collection with normal, contested, unknown, stale, scoped, syndicated and malicious examples. Have at least two annotators review a subset and adjudicate disagreements. No current achieved performance is implied.

# 10. Acceptance test scenarios

| Test ID | Scenario                                                                 | Expected result                                              |
|---------|--------------------------------------------------------------------------|--------------------------------------------------------------|
| AT-01   | Researcher creates same run twice with same idempotency key              | One durable logical run                                      |
| AT-02   | Tenant A requests Tenant B report, evidence and cached query             | All private content denied                                   |
| AT-03   | One of three adapters times out                                          | Run shows failure/partial coverage and stays inspectable     |
| AT-04   | Report sentence cites unrelated passage                                  | Sentence blocked/revised or explicitly marked uncertain      |
| AT-05   | Two articles share syndication upstream                                  | Not counted as independent confirmation                      |
| AT-06   | Conflicting evidence across scoped sources                               | Disputed verdict and review context shown                    |
| AT-07   | User cancels long-running investigation                                  | Cancellation reflected at checkpoint; no duplicate artifacts |
| AT-08   | Malicious webpage attempts instruction override or private-network fetch | Injected command ignored; disallowed fetch blocked           |
| AT-09   | Reviewer updates assessment                                              | New review trace recorded; source snapshot unchanged         |
| AT-10   | User exports version 1 after version 2 exists                            | Version 1 manifest and passages remain reproducible          |

# 11. Delivery mapping and priorities

| Phase          | Priority SRS coverage                                   |
|----------------|---------------------------------------------------------|
| 0 (weeks 1–2)  | FR-001, FR-012, NFR-007/015 and cross-tenant regression |
| 1 (weeks 3–4)  | FR-002–005, FR-018, NFR-001–006                         |
| 2 (weeks 5–8)  | FR-007–016, DATA-03–07, NFR-010–012                     |
| 3 (weeks 9–12) | FR-017/019, labeled evaluation, monitoring and pilots   |

# 12. Traceability to business requirements

| Business requirement | SRS mapping            |
|----------------------|------------------------|
| BR-01                | FR-002, FR-003         |
| BR-02                | FR-004, FR-005         |
| BR-03                | FR-007–010, FR-015–016 |
| BR-04                | FR-010–012             |
| BR-05                | FR-012, NFR-015        |
| BR-06                | FR-013–014             |
| BR-07                | FR-015–016             |
| BR-08                | FR-001, NFR-007–009    |
| BR-09                | FR-017                 |
| BR-10                | FR-004, NFR-010        |
| BR-11                | FR-002, NFR-004        |
| BR-12                | Section 9 and AT-01–10 |

# 13. Open specifications requiring owner decisions

- Exact numerical latency, concurrency, uptime and retention SLAs are not defined in the source and require validation.

- Final role matrix, report export formats, review/approval rules and monitor scheduling quotas require product decisions.

- The proposed interface and table schema are conceptual contracts, not production-verified implementations.

- Confirm source-specific licensing and provider availability at runtime before enabling acquisition.

# 14. References and status

Source: CredenceAI project definition and product/architecture specification, proposed v2.0 (14 October 2026), including sections 5–16 and 19–21. The referenced existing MVP is reported rather than comprehensively verified; this SRS specifies proposed v2 behavior.
