# CredenceAI 2.0 — Comprehensive Implementation Plan & Execution Roadmap

> **Status:** Active Execution Plan  
> **Target Release:** CredenceAI 2.0 MVP (Free-first, Evidence-First Research Intelligence Platform)  
> **Primary Architecture:** Modular Monolith (FastAPI) + Independently Deployed Durable Celery Workers + PostgreSQL + S3-compatible Object Storage + React Research Workspace  
> **Source Documents:** `CredenceAI 2.0.md`, `architecture.md`, `brd.md`, `checklist.md`, `srs.md`  

---

## 1. Executive Summary & Paradigm Shift

CredenceAI 2.0 transitions the platform from a search-ranking aggregator with heuristic confidence scores to an **evidence-first, provenance-anchored research intelligence platform**.

### Core Tenets of v2:
1. **Provenance by Construction:** Every material claim must be backed by an inspectable, immutable, rights-permitted passage from an authorized snapshot, or explicitly flagged as `insufficient_evidence` / `uncertain`.
2. **Elimination of "Truth Probability Theater":** No heuristic search score or classifier output shall be presented as an objective probability of real-world truth. Verdicts are strictly run-scoped: `supported`, `disputed`, `insufficient_evidence`, `not_assessed`.
3. **Multi-Source Honesty:** Source selection routes only to enabled, healthy, policy-compatible adapters. Adapter timeouts, skips, and failures are explicitly reported in coverage diagnostics rather than masked.
4. **Durable, Idempotent Execution:** Research runs execute via transactional outbox dispatch and idempotent worker tasks with hard resource budgets (time, bytes, pages, model tokens).
5. **Absolute Tenant Isolation:** Authorization context (`AuthContext`) derived on the server enforces workspace boundaries across SQL queries, derived full-text search indexes, caches, blob storage, and exports.
6. **Backward Compatibility:** Existing v1 endpoints (`/api/jobs`, `/api/search`, etc.) and historical records remain fully operational via additive schema migrations.

---

## 2. Release Gate Matrix (Hard Go/No-Go Gates)

| Gate | Title | Pass Criteria | Target Phase |
|---|---|---|---|
| **G1** | Scope Alignment | MVP boundaries respected; truth-oracle / unbounded agents / premature microservices excluded. | Phase 0 |
| **G2** | Tenant Isolation | Zero unauthorized cross-workspace data retrieval across API, DB, cache, and exports. | Phase 0 |
| **G3** | Source Execution | Real multi-source router dispatching ≥3 executable source classes with telemetry. | Phase 1 |
| **G4** | Pipeline Durability | Transactional outbox, independent workers, at-least-once safety, cancellation tested. | Phase 1 |
| **G5** | Provenance & Passages | Content snapshots content-hashed; passage offsets/anchors stable; syndication grouped. | Phase 2 |
| **G6** | Evidence Semantics | Atomic claims linked to passages via typed relations; run-scoped verdicts verified. | Phase 2 |
| **G7** | Citation Integrity | 100% frozen citation resolution; unsupported material assertions blocked/revised. | Phase 2 |
| **G8** | Security & Rights | SSRF protection, prompt injection resilience, content retention compliance tested. | Phase 2 |
| **G9** | End-to-End Workflow | User submits inquiry, views real stages, inspects passages, reviews, exports brief. | Phase 3 |
| **G10** | Operational Readiness | Tracing across API/worker/report; cost ceilings enforced; backups/restore rehearsed. | Phase 3 |
| **G11** | Quality Benchmark | 100–200 question benchmark evaluated; citation support ≥95%; unsupported ≤5%. | Phase 3 |
| **G12** | Stakeholder Sign-Off | Product, Engineering, QA, and Security leads sign off checklist. | Phase 3 |

---

## 3. Implementation Phases & Micro-Step Breakdown

```
Phase 0: Workspace Security & Calibration Guardrails (Gate G2, initial G8)
   ├── Step 0.1: Multi-tenant AuthContext & Session Security
   ├── Step 0.2: Tenant & Workspace Schema Migration (additive)
   ├── Step 0.3: Elimination of Misleading Confidence Scores & Copy Update
   └── Step 0.4: Adversarial Cross-Tenant Security Test Suite

Phase 1: Source Discovery Intelligence & Durable Worker Pipeline (Gates G3, G4)
   ├── Step 1.1: Typed SourceAdapter Protocol & Versioned Manifest Registry
   ├── Step 1.2: Three Executable Public Adapters (Reference, Web, Scholarly)
   ├── Step 1.3: Health-Aware Source Router with Full Coverage Diagnostics
   ├── Step 1.4: Research Run State Machine & Transactional Outbox Schema
   └── Step 1.5: Outbox Dispatcher, Celery Task Pipeline, Budgets & Cancellation

Phase 2: Evidence Engine, Passage Integrity & Frozen Reporting (Gates G5, G6, G7, G8)
   ├── Step 2.1: Policy-Gated Acquisition & SSRF/Rebinding Protections
   ├── Step 2.2: Immutable Snapshots, Passage Anchors & Syndication Lineage
   ├── Step 2.3: Atomic Claim Extractor & Scoped Proposition Models
   ├── Step 2.4: Claim-Passage Relation Engine (5 Typed Labels)
   ├── Step 2.5: Run-Scoped Verdict Aggregator & Honest Abstention
   ├── Step 2.6: Citation-Validated Frozen Report Generator Gate
   └── Step 2.7: Human Review Annotation & Audit Trail

Phase 3: Web UI Workspace, TypeScript SDK v2, Monitors & Release Ops (Gates G9-G12)
   ├── Step 3.1: FastAPI v2 REST API Surface (/api/v2/research-runs, /reports, etc.)
   ├── Step 3.2: TypeScript SDK v2 Upgrade with Async Run & Evidence Models
   ├── Step 3.3: React Research Workspace UI (Stages, Inspector, Findings, Briefs)
   ├── Step 3.4: Scheduled Monitors & Evidence Delta Engine
   ├── Step 3.5: Benchmark Evaluation Suite (100-200 Questions & Quality Metrics)
   └── Step 3.6: Deployment Readiness, OpenTelemetry Tracing & Operational Runbooks
```

---

## Phase 0: Workspace Security & Calibration Guardrails

### Micro-Step 0.1: Multi-Tenant `AuthContext` & Session Security
- **Objective:** Create a unified server-derived authorization context. Request handlers must never trust client-supplied tenant/workspace IDs without verifying membership.
- **Components to Create/Update:**
  - `backend/src/app/identity/auth_context.py`: `AuthContext` dataclass containing `user_id`, `tenant_id`, `workspace_id`, `roles`, `permissions`.
  - `backend/src/app/identity/dependencies.py`: FastAPI dependency `get_auth_context` extracting JWT or API key and verifying workspace membership.
- **Acceptance Criteria:**
  - Any request attempting to supply an arbitrary `workspace_id` not belonging to the authenticated principal receives `403 Forbidden`.
  - Scoped API keys resolve to their bound workspace.

### Micro-Step 0.2: Tenant & Workspace Schema Migration (Additive)
- **Objective:** Introduce `tenants`, `workspaces`, `memberships`, `audit_events` tables while preserving existing `users`, `jobs`, `collections`, `monitors`.
- **Components to Create/Update:**
  - `backend/src/app/models.py`: Add `Tenant`, `Workspace`, `Membership`, `AuditEvent` models. Add foreign keys `workspace_id` to existing models where applicable, with default migration fallback to personal default workspaces.
  - `backend/migrations/versions/`: Alembic migration script for tenancy.
- **Acceptance Criteria:**
  - Existing database records seamlessly upgrade; no user or historical job data is orphaned or dropped.
  - Workspace role constraints (`admin`, `researcher`, `reviewer`, `viewer`) are enforced.

### Micro-Step 0.3: Elimination of Misleading Confidence Scores & Copy Update
- **Objective:** Implement ADR-004 and FR-012. Strip any presentation of search rank or heuristic similarity as "truth probability" or "confidence in fact".
- **Components to Create/Update:**
  - `backend/src/app/services/quality_scorer.py`: Rename/refactor heuristic scores to `relevance_score` and `source_quality_indicator`, disclaiming factual veracity.
  - `backend/src/app/services/synthesis.py`: Update prompts and outputs to use "supported by evidence examined" phrasing instead of "verified true".
- **Acceptance Criteria:**
  - Zero API responses or UI strings describe search scores as "factual certainty".
  - Code and docstrings reflect calibrated evidence terminology.

### Micro-Step 0.4: Adversarial Cross-Tenant Security Test Suite
- **Objective:** Validate Release Gate G2. Ensure total isolation across database, search indexes, cache, and exports.
- **Components to Create/Update:**
  - `backend/tests/test_tenant_isolation_adversarial.py`:
    - Scenario A: Tenant A attempts to fetch Tenant B's job/run by ID -> `404 Not Found` or `403 Forbidden`.
    - Scenario B: Tenant A runs search query; results must never include Tenant B's private documents or snapshots.
    - Scenario C: Cache key collision attempts across workspaces; verify cache keys include `workspace_id`.
- **Acceptance Criteria:**
  - 100% of adversarial tenant tests pass with zero leakage.

---

## Phase 1: Source Discovery Intelligence & Durable Worker Pipeline

### Micro-Step 1.1: Typed `SourceAdapter` Protocol & Versioned Manifest Registry
- **Objective:** Implement FR-004 and SRC-01/02. Define an extensible, strictly typed adapter interface with manifests declaring capabilities, timeouts, quotas, and legal constraints.
- **Components to Create/Update:**
  - `backend/src/app/sources/protocol.py`: `SourceAdapter` abstract base class with `async def search(query, filters, budget) -> AdapterResponse`.
  - `backend/src/app/sources/manifest.py`: `AdapterManifest` schema (`source_id`, `version`, `source_class`, `enabled`, `executable`, `timeout_seconds`, `rate_limit_per_minute`, `cost_per_query`, `legal_restrictions`).
  - `backend/src/app/sources/registry.py`: Central registry managing active adapters.

### Micro-Step 1.2: Three Executable Public Adapters (Reference, Web, Scholarly)
- **Objective:** Fulfill Gate G3 and SRC-06. Ensure at least three distinct source classes run reliably in integration tests without external paid keys.
- **Components to Create/Update:**
  - Reference Class: `backend/src/app/sources/adapters/wikipedia_adapter.py` (Wikipedia REST API & Wikidata entity discovery).
  - Web Class: `backend/src/app/sources/adapters/duckduckgo_adapter.py` / `searxng_adapter.py` (open web discovery).
  - Scholarly Class: `backend/src/app/sources/adapters/openalex_adapter.py` / `crossref_adapter.py` (scholarly paper & metadata discovery).
  - Integration Fixtures: Recorded VCR/cassette mocks and live integration tests in `backend/tests/sources/`.

### Micro-Step 1.3: Health-Aware Source Router with Full Coverage Diagnostics
- **Objective:** Implement FR-004/005 and SRC-12/13. Route queries based on intent, language, vertical, and budget, recording full coverage telemetry.
- **Components to Create/Update:**
  - `backend/src/app/sources/router.py`: Determines eligible adapters; executes parallel queries under bounded timeouts.
  - Records coverage manifest: `queried_adapters`, `skipped_adapters` (with reason: disabled, budget_exceeded, policy), `failed_adapters` (timeout, network error).
- **Acceptance Criteria:**
  - Provider timeouts yield truthful partial results and coverage notes, never silent failures.

### Micro-Step 1.4: Research Run State Machine & Transactional Outbox Schema
- **Objective:** Implement FR-002, FR-003, NFR-001, and DATA-02.
- **Components to Create/Update:**
  - `backend/src/app/models.py`:
    - `ResearchRun`: `id`, `workspace_id`, `author_id`, `question`, `mode`, `budget`, `status`, `idempotency_key`, `config_version`.
    - `RunStep`: `id`, `run_id`, `step_key`, `state`, `attempt_count`, `duration_ms`, `error_type`, `error_message`.
    - `OutboxEvent`: `id`, `aggregate_type`, `aggregate_id`, `event_type`, `payload`, `status`, `created_at`, `processed_at`.
  - Atomicity helper: `create_research_run_with_outbox(session, run_data)`.

### Micro-Step 1.5: Outbox Dispatcher, Celery Task Pipeline, Budgets & Cancellation
- **Objective:** Satisfy Gate G4 and RUN-01 to RUN-13.
- **Components to Create/Update:**
  - `backend/src/app/infrastructure/outbox_dispatcher.py`: Periodic worker process polling unhandled outbox events and dispatching to Celery.
  - `backend/src/app/research/tasks.py`: Celery tasks for stages: `planning`, `retrieving`, `extracting`, `normalizing`, `verifying`, `reporting`.
  - Cancellation checkpoint helper: Checks `is_run_cancelled(run_id)` before heavy I/O or model calls.
  - Budget manager: Tracks wall-clock time, bytes fetched, page counts, and token consumption against run limits.

---

## Phase 2: Evidence Engine, Passage Integrity & Frozen Reporting

### Micro-Step 2.1: Policy-Gated Acquisition & SSRF/Rebinding Protections
- **Objective:** Implement FR-006, NFR-009, and PRV-01 to PRV-04.
- **Components to Create/Update:**
  - `backend/src/app/acquisition/ssrf_guard.py`:
    - DNS resolution validation before connect.
    - Connect-time IP check blocking `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16` (link-local/metadata), IPv6 loopback/link-local.
    - Redirect validation ensuring secondary hops are also re-checked.
  - `backend/src/app/acquisition/http_fetcher.py`: Respects `robots.txt`, enforces MIME type allowlist, max byte limit (default 5MB), and decompression bomb checks.

### Micro-Step 2.2: Immutable Snapshots, Passage Anchors & Syndication Lineage
- **Objective:** Implement FR-007, FR-008, FR-011, DATA-03/04, Gate G5.
- **Components to Create/Update:**
  - `backend/src/app/models.py`:
    - `Source`: canonical URL, publisher, source_class, syndication_upstream_id.
    - `Snapshot`: `snapshot_id`, content SHA-256 hash, rights/license classification, object storage URI or permitted excerpt.
    - `Passage`: `passage_id`, `snapshot_id`, `text_content`, `char_offset_start`, `char_offset_end`, `passage_hash`.
  - Lineage deduplicator: Detects wire service republishing (e.g. AP/Reuters syndication) and groups them so duplicated articles do not inflate independent corroboration counts.

### Micro-Step 2.3: Atomic Claim Extractor & Scoped Proposition Models
- **Objective:** Implement FR-009 and DATA-05.
- **Components to Create/Update:**
  - `backend/src/app/evidence/claim_extractor.py`: Breaks complex statements into atomic propositions preserving subject, predicate, object/value, units, geographic scope, timeframe, and origin (`user_submitted` vs `source_extracted`).

### Micro-Step 2.4: Claim-Passage Relation Engine (5 Typed Labels)
- **Objective:** Implement FR-010, EVD-05, and Gate G6.
- **Components to Create/Update:**
  - `backend/src/app/evidence/relation_engine.py`: Evaluates claim-passage pairs into exact typed labels: `supports`, `contradicts`, `mentions`, `irrelevant`, `uncertain`.
  - Deterministic sanity checks: Verifies numeric compatibility, date order consistency, and geographical match before assigning `supports`.

### Micro-Step 2.5: Run-Scoped Verdict Aggregator & Honest Abstention
- **Objective:** Implement FR-012, EVD-10, EVD-12.
- **Components to Create/Update:**
  - `backend/src/app/evidence/verdict_service.py`: Computes run-scoped verdict:
    - `supported`: Strong supporting passages, no unresolved material contradiction.
    - `disputed`: Conflicting passages from credible sources detected.
    - `insufficient_evidence`: Evidence missing, ambiguous, or unconfirmed.
    - `not_assessed`: Out of scope or budget exhausted before evaluation.

### Micro-Step 2.6: Citation-Validated Frozen Report Generator Gate
- **Objective:** Implement FR-015, FR-016, and Release Gate G7.
- **Components to Create/Update:**
  - `backend/src/app/reporting/report_generator.py`: Generates draft research briefs referencing frozen passage IDs.
  - `backend/src/app/reporting/citation_validator.py`: Enforces 100% citation resolution against authorized frozen passages. Rejects/revises unsupported statements. Computes cryptographic `manifest_hash`.
  - `Report` model: Stores frozen version, manifest hash, markdown/json representation, and publication status.

### Micro-Step 2.7: Human Review Annotation & Audit Trail
- **Objective:** Implement FR-013, FR-014, and BR-06.
- **Components to Create/Update:**
  - `backend/src/app/evidence/review_service.py`: Allows authorized researchers/reviewers to annotate findings, dispute relations, or approve reports.
  - Audit trail preserves reviewer ID, timestamp, and rationale without modifying immutable source snapshot records.

---

## Phase 3: Web UI Workspace, TypeScript SDK v2, Monitors & Release Ops

### Micro-Step 3.1: FastAPI v2 REST API Surface
- **Objective:** Deliver clean, documented endpoints adhering to SRS Section 4:
  - `POST /api/v2/research-runs`
  - `GET /api/v2/research-runs/{run_id}`
  - `GET /api/v2/research-runs/{run_id}/sources`
  - `GET /api/v2/research-runs/{run_id}/claims`
  - `GET /api/v2/research-runs/{run_id}/claims/{claim_id}/evidence`
  - `GET /api/v2/research-runs/{run_id}/reports/{version}`
  - `POST /api/v2/research-runs/{run_id}/reviews`
  - `POST /api/v2/research-runs/{run_id}/cancel`
  - `POST /api/v2/monitors`
  - `GET /api/v2/monitors/{monitor_id}/deltas`

### Micro-Step 3.2: TypeScript SDK v2 Upgrade
- **Objective:** Implement typed client methods, models, and error handlers matching the v2 API contract.
- **Components to Update:**
  - `sdk/src/services/research_runs.ts`
  - `sdk/src/types/research.ts`
  - `sdk/src/types/evidence.ts`
  - `sdk/test/research_runs.test.ts`

### Micro-Step 3.3: React Research Workspace UI
- **Objective:** Create a premium, dynamic web workspace adhering to Design Aesthetics and SRS Section 8:
  - Research Home: Question input, research modes (Discover, Investigate, Deep Investigation), budget selectors.
  - Run Progress View: Live animated stage stepper, provider coverage breakdown, partial-state diagnostics.
  - Findings Board: Claims categorized by verdict badge with conflict callouts.
  - Evidence Inspector: Side-by-side view highlighting exact passage text, publisher badge, retrieval date, and syndication notes.
  - Report Workspace: Frozen brief viewer, interactive citation badges linking to passages, markdown/json export, reviewer approval actions.

### Micro-Step 3.4: Scheduled Monitors & Evidence Delta Engine
- **Objective:** Implement FR-017, MON-01 to MON-07.
- **Components to Update:**
  - `backend/src/app/monitoring/scheduler.py`: Triggers scheduled reruns with isolated execution.
  - `backend/src/app/monitoring/delta_engine.py`: Computes diffs between runs: new passages, altered claims, modified verdicts.

### Micro-Step 3.5: Benchmark Evaluation Suite
- **Objective:** Fulfill QA-01 to QA-08 and Gate G11.
- **Components to Create:**
  - Benchmark dataset runner with 100+ questions covering normal, contested, stale, syndicated, and adversarial queries.
  - Evaluation reporting scripts outputting citation support rate, precision/recall per relation class, and cost per run.

### Micro-Step 3.6: Deployment Readiness, Telemetry & Operational Runbooks
- **Objective:** Fulfill Gates G10 & G12.
- **Components to Update:**
  - OpenTelemetry trace propagation across API, Outbox, Celery, and Evaluator.
  - Backup & restore rehearsal scripts for PostgreSQL and snapshots.
  - Operational runbook and final checklist sign-off document.

---

## 4. Implementation Status Ledger (ISL)

| Item | Phase | Status | Evidence / Test | Assigned Role |
|---|---|---|---|---|
| **0.1** AuthContext & Session Security | Phase 0 | **Done** | `backend/tests/test_auth_context.py` (4/4 PASS) | Architect / Backend |
| **0.2** Workspace & Tenancy Migration | Phase 0 | **Done** | `backend/src/app/models.py` (Tenant, Workspace, Membership, AuditEvent) | Backend |
| **0.3** Misleading Score Elimination | Phase 0 | **Done** | `quality_scorer.py` & `synthesis.py` (ADR-004 verified) | Backend |
| **0.4** Adversarial Tenant Isolation Suite | Phase 0 | **Done** | `test_tenant_isolation_adversarial.py` (Gate G2: PASS) | Security / QA |
| **1.1** SourceAdapter Protocol & Registry | Phase 1 | **Done** | `protocol.py` & `registry.py` | Backend |
| **1.2** 3 Executable Public Adapters | Phase 1 | **Done** | Wikipedia, Web/SearXNG, OpenAlex (Gate G3: PASS) | Backend |
| **1.3** Health-Aware Source Router | Phase 1 | **Done** | `test_source_routing.py` (AT-03 Partial Coverage PASS) | Backend |
| **1.4** Research Run State & Outbox Model | Phase 1 | **Done** | `test_research_pipeline.py` (AT-01 Idempotency PASS) | Backend |
| **1.5** Outbox Dispatcher & Workers | Phase 1 | **Done** | `test_research_pipeline.py` (Gate G4 & AT-07 PASS) | Backend / DevOps |
| **2.1** Acquisition Policy & SSRF Guard | Phase 2 | **Done** | `test_evidence_engine.py::test_ssrf_guard_*` (Gate G8 PASS) | Security / Backend |
| **2.2** Snapshots, Passages & Lineage | Phase 2 | **Done** | `test_evidence_engine.py::test_syndication_*` (Gate G5 PASS) | Backend |
| **2.3** Atomic Claim Extractor | Phase 2 | **Done** | `test_evidence_engine.py::test_claim_extractor_*` | Backend |
| **2.4** Evidence Relation Engine (5 labels) | Phase 2 | **Done** | `test_evidence_engine.py::test_relation_engine_*` (Gate G6 PASS) | Backend |
| **2.5** Run-Scoped Verdict Evaluator | Phase 2 | **Done** | `test_evidence_engine.py::test_verdict_service_*` (Calibrated Abstention PASS) | Backend |
| **2.6** Citation-Validated Report Gate | Phase 2 | **Done** | `test_evidence_engine.py::test_gate_g7_*` (Gate G7 & AT-04 PASS) | Backend |
| **2.7** Human Review Annotation & Audit | Phase 2 | **Done** | `test_evidence_engine.py::test_human_review_*` (BR-06 PASS) | Backend |
| **3.1** FastAPI v2 REST API Surface | Phase 3 | **Done** | `test_api_v2_research_runs.py` (All 2/2 PASS) | Backend |
| **3.2** TypeScript SDK v2 Upgrade | Phase 3 | **Done** | `sdk/test/research_runs.test.ts` (All 25/25 PASS) | Frontend / SDK |
| **3.3** React Research Workspace UI | Phase 3 | **Done** | `ResearchWorkspace.tsx` + Production Vite Build PASS | Frontend |
| **3.4** Monitors & Evidence Deltas | Phase 3 | **Done** | `test_v2_monitors_crud_and_deltas` PASS | Backend |
| **3.5** Benchmark Evaluation Suite | Phase 3 | Ready | Benchmark evaluator scaffold | QA / Researcher |
| **3.6** Ops Telemetry & Release Verification | Phase 3 | Ready | Final verification & runbook sign-off | DevOps / QA |
