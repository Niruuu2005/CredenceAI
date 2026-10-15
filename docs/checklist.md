# CredenceAI 2.0 — 100% Completion & Release Checklist

> **Release target:** CredenceAI 2.0 MVP for student/campus and community fact-checking teams  
> **Baseline:** `project (3).md` (project definition v2.0, 14 Oct 2026), `architecture.md` (target architecture), `CredenceAI_BRD.docx`, `CredenceAI_SRS.docx`  
> **Status:** Acceptance checklist; unchecked items are **not** evidence of implementation  
> **Architecture:** Modular monolith (FastAPI) + independently deployed durable Celery workers; microservices are **not** a release requirement.  
> **Review:** Maintain a release evidence folder and record approval in the sign-off section below.

## 0. Rules for interpreting “100% complete”

**Definition:** The **CredenceAI 2.0 MVP is complete** only when **all mandatory (M) checkboxes** below are checked *with linked, current evidence*, all critical/high release-blocking defects are closed, each **release gate** passes, and the final sign-offs are recorded. A checked task without test evidence does **not** count. This establishes completion **for the defined v2 MVP scope**, not every future product capability or universal factual accuracy.

- `[ ]` means not proven complete. Check an item only after its **observable outcome**, tests and evidence are verified in a deployment representative of release.
- Every item in sections **1–17** is **mandatory (M)** unless explicitly labelled **(O) optional**. Do not waive mandatory items solely to make the percentage reach 100%.
- Store proof as a PR/commit, test report, screen recording, issue, exported artifact, dashboard snapshot or signed review; add a link in your issue tracker or in the evidence register below.
- **Not applicable (N/A)** may only be recorded for genuinely conditional subcases (such as an optional model provider not configured), with rationale, owner and reviewer approval. Mandatory platform behavior may not be marked N/A.
- **Go/no-go overrides percentage:** any known cross-tenant leak, exploitable SSRF path, unapproved content retention, report with unresolved fabricated citation, broken rollback or data loss blocks release even if every box is checked.
- A benchmark percentage is measured on the agreed frozen dataset, not estimated from demo examples. Proposed targets below must be validated or formally revised **before** the release evaluation begins.
- `100%` is calculated only after release scope is frozen and reviewer-approved. Do not remove failed items from the denominator.

### Release scorecard (fill when reviewing)

| Metric | Value |
|---|---|
| Mandatory controls in scope | `TBD` |
| Mandatory controls verified complete | `TBD` |
| Mandatory completion | `verified / in-scope × 100` |
| Open critical / high blocking issues | `TBD / TBD` |
| Passed / total release gates | `TBD / TBD` |
| Human pilot acceptance | `Pending / Pass / Fail` |
| Final release decision | `NO-GO` until all gates and approvals pass |

## 1. Product scope, governance and business value

- [ ] **GOV-01** Product owner approves the v2 MVP boundary, primary campus/community fact-checking users and expected workflow. Evidence: signed release scope.
- [ ] **GOV-02** User personas and a representative claim-verification journey are documented and tested with target users.
- [ ] **GOV-03** Discover, Investigate and Deep Investigation behaviors, limits and outputs are specified and consistent across UI/API/docs.
- [ ] **GOV-04** Monitoring is included only at the scheduled, configured cadence; no unsupported continuous-monitoring claim appears.
- [ ] **GOV-05** V2 non-goals are explicit in roadmap and launch copy: truth oracle, unbounded agents, microservice fleet, proprietary model, enterprise SSO/compliance certifications.
- [ ] **GOV-06** Product language says **“supported by evidence examined”** rather than objectively verified true; reviewers approve sample findings.
- [ ] **GOV-07** Each requirement has unique ID, owner, priority, implementation reference, test reference and outcome.
- [ ] **GOV-08** Baseline release configuration, API schema, model/rule versions and data migrations are version tagged.
- [ ] **GOV-09** Severity definitions, bug-triage owner and a clear go/no-go decision process are documented.
- [ ] **GOV-10** Release notes distinguish functioning features, known limitations, provider caveats and future plans.

## 2. Identity, permissions and tenant isolation

- [ ] **IAM-01** Every private API endpoint requires authentication or a documented approved public-access exception.
- [ ] **IAM-02** Workspace and tenant scope is derived from verified server-side `AuthContext`, never trusted from a client-selected ID alone.
- [ ] **IAM-03** Roles and membership permissions are enforced for read, create, update, review, export, share and delete actions.
- [ ] **IAM-04** Cross-tenant access to jobs, research runs, sources, passages, claims, collections and monitor records is denied by integration tests.
- [ ] **IAM-05** Search through PostgreSQL and any enabled OpenSearch/vector index enforces workspace and rights visibility.
- [ ] **IAM-06** Cache keys carry access/rights scope and cache hits re-check authorization; cross-tenant cache poisoning tests pass.
- [ ] **IAM-07** Report and object-storage access, signed download URLs and shared exports enforce authorization and expiry.
- [ ] **IAM-08** Tenant-scoped pagination, counts, filters, batch requests and error messages cannot expose private existence or metadata.
- [ ] **IAM-09** API keys are scoped, securely hashed, shown once, revocable and rotatable; revoked keys stop working.
- [ ] **IAM-10** Credentials/session secrets are not exposed in logs, front-end bundles, telemetry, exceptions or repository history.
- [ ] **IAM-11** Public rights-cleared data is isolated from private workspace material in indexes and storage.
- [ ] **IAM-12** Unauthorized read/write regression suite passes across all public-facing resource types; **zero known cross-tenant retrieval**.

## 3. Source discovery, adapters and routing

- [ ] **SRC-01** A typed `SourceAdapter` protocol and versioned manifest are implemented and documented.
- [ ] **SRC-02** Manifest records enabled, executable, capabilities, source class, language, limits, timeout, costs and legal constraints.
- [ ] **SRC-03** Router selects only configured, executable, healthy and policy-compatible source adapters.
- [ ] **SRC-04** Selection considers query intent, geography, language, freshness, quota and per-run budgets.
- [ ] **SRC-05** Selection actually controls network requests; no hidden fixed-provider-only execution path remains for v2.
- [ ] **SRC-06** At least **three executable source classes** run on suitable integration fixtures with actual adapter-call telemetry.
- [ ] **SRC-07** Public source candidates (web, reference, news, scholarly, archive) are each marked **implemented, disabled or unavailable**; no phantom provider is advertised.
- [ ] **SRC-08** Provider timeouts, bounded concurrency, rate limits and retry ceilings are enforced and tested.
- [ ] **SRC-09** Source response normalization includes URL, publisher, source class, fetch time, provider and coverage notes.
- [ ] **SRC-10** Duplicate/canonical URLs are normalized without collapsing independently published evidence.
- [ ] **SRC-11** Original reporting, republishing, quotation and syndication lineage can be stored and inspected.
- [ ] **SRC-12** Source coverage explicitly states queried, skipped, timed-out, failed and unavailable adapters with reasons.
- [ ] **SRC-13** Provider outages/rate limiting yield truthful partial results rather than silent success or invented coverage.
- [ ] **SRC-14** Discovery ranking/reliability scores are clearly separated from factual support assessments.

## 4. Fetching, content rights and provenance

- [ ] **PRV-01** Fetch policy checks allowable scheme, robots/provider terms, rate limits and content retention rights.
- [ ] **PRV-02** Only HTTP(S) fetches are allowed; loopback, private, link-local, metadata and reserved IPs are blocked.
- [ ] **PRV-03** DNS resolution, redirects and connection destination are validated against SSRF/rebinding bypasses.
- [ ] **PRV-04** Time, response-size, decompression, MIME/content-type and extraction-resource limits are enforced.
- [ ] **PRV-05** Restricted extraction workers do not receive privileged service credentials.
- [ ] **PRV-06** Source records preserve original/canonical URLs, publisher, provider, source class and rights metadata.
- [ ] **PRV-07** Publication time and retrieval time remain separate fields; missing/uncertain publication dates are identified.
- [ ] **PRV-08** Immutable, content-hashed `snapshot_id` records reference permitted stored content or excerpts.
- [ ] **PRV-09** Snapshot/excerpt retention rules prevent unauthorized full-text storage or export.
- [ ] **PRV-10** Each passage persists `snapshot_id`, accessible text/rights-permitted quote, stable offset/anchor, hash and extraction version.
- [ ] **PRV-11** Evidence remains resolvable after source change/deletion within documented rights and retention restrictions; unavailable content is clearly flagged.
- [ ] **PRV-12** Rights takedown, expiry, deletion, backups and derived-index cleanup are tested end-to-end.

## 5. Durable research execution

- [ ] **RUN-01** Research run creation records workspace, author, question, filters, mode, budgets, status and config version.
- [ ] **RUN-02** Create-run and outbox event are persisted atomically before dispatch.
- [ ] **RUN-03** Independently deployed workers receive queued tasks; production does not rely on request-thread background execution.
- [ ] **RUN-04** Status lifecycle supports `created`, `queued`, `planning`, `retrieving`, `extracting`, `normalizing`, `verifying`, `reporting` and terminal outcomes.
- [ ] **RUN-05** `completed`, `partial`, `failed`, `cancelled` and `timed_out` have documented transition/response semantics.
- [ ] **RUN-06** Delivery is at-least-once safe: repeated tasks with the same `(run_id, step_key, input_version)` do not duplicate outputs.
- [ ] **RUN-07** Step attempts, errors, timestamps, duration and retry counts are queryable for a run.
- [ ] **RUN-08** Worker claim/lease expiration, stalled-task recovery and reconciliation are exercised by forced-kill tests.
- [ ] **RUN-09** Exponential retry/backoff and per-provider retry constraints prevent runaway load.
- [ ] **RUN-10** Per-run source, page, document, wall-clock, byte, token and cost budgets are capped and tested.
- [ ] **RUN-11** Cancellation checkpoints stop remaining work and preserve a trustworthy terminal state.
- [ ] **RUN-12** Concurrent runs and duplicate HTTP submissions respect idempotency keys and tenant scope.
- [ ] **RUN-13** Partial providers, model timeouts, storage unavailability and queue restart produce recoverable, observable outcomes.

## 6. Evidence and claim assessment (core release blocker)

- [ ] **EVD-01** Candidate claims are atomic and retain verbatim wording, origin, extractor/rule version and provenance.
- [ ] **EVD-02** Claim data records subject, predicate, object/value, units, geographic/population scope, timeframe and conditions where applicable.
- [ ] **EVD-03** User-entered claims and claims extracted from third-party material have distinguishable origin types.
- [ ] **EVD-04** `claim_evidence` links an existing claim to an existing, authorized passage ID.
- [ ] **EVD-05** Evidence relations support exactly defined labels: `supports`, `contradicts`, `mentions`, `irrelevant`, `uncertain`.
- [ ] **EVD-06** Each evidence edge preserves rationale, method/model version, source-independence grouping and review state.
- [ ] **EVD-07** Relation assessment performs feasible temporal, geographic, numerical, unit and scope-consistency checks.
- [ ] **EVD-08** Model/NLI output is treated as a proposal; schema and deterministic checks cannot be bypassed by retrieved content.
- [ ] **EVD-09** Evidence review exposes independent original publishers versus syndicated repetitions; syndicated sources are not counted as independent confirmations.
- [ ] **EVD-10** Verdicts are **run-scoped**: `supported`, `disputed`, `insufficient_evidence`, `not_assessed`.
- [ ] **EVD-11** Material conflicts yield `disputed` or flagged review, not silently reconciled statements.
- [ ] **EVD-12** Missing, inaccessible, out-of-scope or weak evidence causes transparent abstention, never a fabricated truth score.
- [ ] **EVD-13** No `final_trust_score`, static confidence default or search rank is presented as calibrated probability of truth.
- [ ] **EVD-14** Human reviewer can annotate/accept/reject proposed assessments while preserving immutable original evidence and audit history.
- [ ] **EVD-15** Review state includes actor, timestamp and rationale; unauthorized reviewers are blocked.
- [ ] **EVD-16** An adversarial set of contradictory dates, percentages, regions and quoted text demonstrates correct disagreement/abstention behavior.

## 7. Reports, citations and exports

- [ ] **RPT-01** Report generation uses approved claim/passage links, not free-floating generated prose as evidence.
- [ ] **RPT-02** Each material report statement has an inspectable authorized **frozen** passage citation or is explicitly marked uncertain/unassessed.
- [ ] **RPT-03** Citation resolution is **100%** against authorized passage IDs in the frozen report manifest.
- [ ] **RPT-04** Validators detect nonexistent citations, unrelated passages, malformed quote spans, unsupported figures and incompatible dates.
- [ ] **RPT-05** Unsupported material assertions are blocked, revised, removed or prominently flagged before final report approval.
- [ ] **RPT-06** Reports include retrieval/publication dates, source coverage, source limitations, conflicts and uncertainty.
- [ ] **RPT-07** Frozen report stores version, configuration/evaluation version, source manifest hash, creation date and approval state.
- [ ] **RPT-08** Re-running an investigation creates new results/versions without silently rewriting a historical approved report.
- [ ] **RPT-09** Basic report view and export render the same claim-to-evidence citations and authorization policy.
- [ ] **RPT-10** Report links reopen authorized source excerpts and explain missing/expired material.
- [ ] **RPT-11** Citation accuracy is tested against human labels, not merely checked for syntactically valid links.

## 8. Web experience and accessibility

- [ ] **UI-01** Research home supports workspace selection, question/claim input, mode and relevant filters.
- [ ] **UI-02** Users can set or view bounded source/time/full-document budgets before starting a run.
- [ ] **UI-03** Run progress displays real stages, selected provider classes, skipped/failed coverage and partial-state warnings.
- [ ] **UI-04** Users can cancel an authorized in-progress run; the UI reflects the persisted status.
- [ ] **UI-05** Findings board lists atomic claims with verdict, assessment context and reviewer state.
- [ ] **UI-06** Evidence inspector shows exact highlighted passage, publisher, date, snapshot/excerpt provenance, relation, independence group and caveats.
- [ ] **UI-07** Source explorer differentiates original sources, aggregators, republications and syndication.
- [ ] **UI-08** Human review controls save annotations safely and show provenance of changes.
- [ ] **UI-09** Report workspace provides version information, citations, export, sharing permissions and approval state.
- [ ] **UI-10** Collections save authorized investigations/evidence; monitors show scheduled runs and changes.
- [ ] **UI-11** Settings show workspace permissions, scoped API keys, quotas, retention and available provider configuration.
- [ ] **UI-12** Loading, zero-results, evidence-insufficient, provider-failure, cancelled and timeout states are understandable.
- [ ] **UI-13** Keyboard navigation, accessible control names, focus behavior, contrast, responsive layouts and screen-reader basics pass documented accessibility checks.
- [ ] **UI-14** Browser regression tests pass on the project-supported browser/device matrix.

## 9. API, SDK and backward compatibility

- [ ] **API-01** `POST /api/v2/research-runs` creates an authorized idempotent asynchronous run.
- [ ] **API-02** `GET /api/v2/research-runs/{run_id}` reports durable status, progress and typed errors.
- [ ] **API-03** `GET /api/v2/research-runs/{run_id}/sources` lists real source coverage and lineage.
- [ ] **API-04** `GET /api/v2/research-runs/{run_id}/claims` lists scoped claims/verdicts.
- [ ] **API-05** `GET /api/v2/research-runs/{run_id}/claims/{claim_id}/evidence` returns accessible relations/passages.
- [ ] **API-06** `GET /api/v2/research-runs/{run_id}/reports/{version}` returns an authorized frozen report.
- [ ] **API-07** `POST /api/v2/research-runs/{run_id}/reviews` records controlled review events.
- [ ] **API-08** `POST /api/v2/research-runs/{run_id}/cancel` supports defined cancellation semantics.
- [ ] **API-09** `POST /api/v2/monitors` and `GET /api/v2/monitors/{monitor_id}/deltas` implement documented scheduled behavior.
- [ ] **API-10** APIs use consistent 401/403/404 handling, schema validation, pagination, limits and machine-readable errors.
- [ ] **API-11** API OpenAPI schema/examples match live behavior; contract tests are generated/run against it.
- [ ] **API-12** TypeScript SDK models async runs, claims, evidence, reports, reviews, and monitor deltas with typed error handling.
- [ ] **API-13** SDK samples build and execute successfully against the v2 test environment.
- [ ] **API-14** Legacy v1 endpoint/mode behavior remains compatible or has an explicitly approved migration notice and tests.

## 10. Persistence, migrations, search and caching

- [ ] **DB-01** PostgreSQL owns canonical application and evidence records; ephemeral caches/indexes are rebuildable.
- [ ] **DB-02** Tenant, workspace, memberships, API key and authorization-related constraints are migrated and tested.
- [ ] **DB-03** `research_runs`, `run_steps`, `source_fetches` and `outbox_events` tables/constraints exist.
- [ ] **DB-04** `sources`, `snapshots`, `passages`, `claims`, `claim_evidence`, `claim_verdicts` and `reports` models exist.
- [ ] **DB-05** Audit events, monitor delta history and collections preserve their access scope and lifecycle.
- [ ] **DB-06** Unique IDs, idempotency keys, foreign keys, immutability/version fields and indexes are validated.
- [ ] **DB-07** Existing users, jobs, normalized results, scores, collections, monitors and keys survive non-breaking migrations.
- [ ] **DB-08** Upgrade from representative v1 data and rollback/recovery are tested in staging on backups.
- [ ] **DB-09** Full-text index covers permitted passage retrieval and filters access scope before returning results.
- [ ] **DB-10** Index rebuild/reconciliation reproduces searchable projections without leaking across tenants.
- [ ] **DB-11** Cache key includes query/filter signature, workspace/rights, providers/config, version and freshness window.
- [ ] **DB-12** Changed evaluation rules invalidate affected derived summaries; expired source content is not served from stale caches.
- [ ] **DB-13** Database backups, object backups, restore validation and deletion/retention lifecycle are verified.

## 11. Monitoring and collections

- [ ] **MON-01** Users can create/view authorized saved collections of research and evidence.
- [ ] **MON-02** Monitor schedule, query, filters, workspace, budget and owner are persisted.
- [ ] **MON-03** Scheduler triggers bounded reproducible reruns with isolated execution/history.
- [ ] **MON-04** Monitor deltas identify new, removed and changed evidence with retrieval time and version context.
- [ ] **MON-05** User can inspect past monitor runs; historical reports are not overwritten.
- [ ] **MON-06** Duplicate scheduled delivery, failed scheduler restarts and missed-task recovery are tested.
- [ ] **MON-07** Disabled/deleted monitors stop scheduling and obey retention policies.

## 12. Safety, privacy and legal readiness

- [ ] **SEC-01** A reviewed threat model covers cross-tenant access, SSRF, prompt injection, unauthorized exports and malicious documents.
- [ ] **SEC-02** External pages and model outputs cannot alter system instructions, authorize tools or exfiltrate internal context.
- [ ] **SEC-03** Inputs/outputs, adapter manifests, tool calls and model results are validated against strict schemas and permissions.
- [ ] **SEC-04** TLS, encryption at rest where supported, secrets management and least-privilege access are configured.
- [ ] **SEC-05** Dependency/security scans run in CI; critical exploitable findings are resolved before release.
- [ ] **SEC-06** Audit logs track who accessed/reviewed/exported/deleted resources without logging excessive sensitive source content.
- [ ] **SEC-07** User-data retention, account/workspace deletion and evidence-copy policies are published and exercised.
- [ ] **SEC-08** Third-party licenses, provider terms, robots requirements and excerpt/export permissions receive review.
- [ ] **SEC-09** Medical/legal/financial/regulatory-use restrictions and uncertainty language are present in applicable UI/docs.
- [ ] **SEC-10** Security regression suite passes SSRF redirect/DNS, cross-tenant cache, injection, key-scope and export-abuse scenarios.

## 13. Observability and operational costs

- [ ] **OPS-01** Every run has correlation/trace ID and records stage, provider coverage, timings, retries and outcomes.
- [ ] **OPS-02** API → outbox → worker → adapter → evidence → report tracing is navigable during incident triage.
- [ ] **OPS-03** Dashboards expose queue age, p50/p95 stage time, completion/partial/failure rates, worker saturation and provider errors.
- [ ] **OPS-04** Quality metrics include passage attribution, citation validity, relation-label performance, independence errors and user corrections.
- [ ] **OPS-05** Cost metrics include model tokens, API calls, fetched bytes, storage, egress and cost per completed run.
- [ ] **OPS-06** Logs are structured, secrets redacted and retention/access permissions enforced.
- [ ] **OPS-07** Alerts and documented response actions cover stuck queue, elevated 5xx, provider outage, storage failures and access-control anomalies.
- [ ] **OPS-08** Per-run hard cost/resource ceilings are visible and empirically enforced under failure/retry scenarios.

## 14. Verification, quality benchmarks and nonfunctional gates

- [ ] **QA-01** Freeze a **100–200 question** human-labelled set covering normal, contested, stale, unknown, temporal/geographic ambiguity, syndication and malicious sources.
- [ ] **QA-02** At least two annotators independently score a representative subset; disagreements are adjudicated and labels/version retained.
- [ ] **QA-03** **100%** of report citations resolve to authorized frozen passage IDs in automated evaluation.
- [ ] **QA-04** **≥95%** of cited material statements are supported by their actual cited passages in held-out human review (proposed release gate).
- [ ] **QA-05** **≤5%** unsupported material claims in initially reviewed generated reports (proposed release gate).
- [ ] **QA-06** Evidence relation classifier precision, recall and confusion matrix are published **per class**; failures are discussed.
- [ ] **QA-07** Original/syndicated-source grouping is evaluated against human-labelled pairs; baseline and approved threshold recorded.
- [ ] **QA-08** Frozen input/config/rule versions reproduce explainable results or explicitly record nondeterminism.
- [ ] **QA-09** Unit tests cover normalization, offsets/hashes, claim scope, numeric/time consistency, permissions and budget policy.
- [ ] **QA-10** Integration tests cover provider fixtures, ACL, outbox, retries, storage, caching and index rebuilding.
- [ ] **QA-11** E2E tests cover create → inspect → review → freeze → export, plus partial providers, cancel, rerun and monitoring.
- [ ] **QA-12** Load/resilience tests include concurrent tenants, slow sources, worker loss, queue burst and object-store failure.
- [ ] **QA-13** p50/p95 latency, resource ceilings and failure rates are measured and compared with **pre-approved** performance/SLO targets.
- [ ] **QA-14** Manual baseline versus product time-to-brief, correction rate and overall task success are documented; no invented improvement percentages.
- [ ] **QA-15** Critical and high severity bug counts are zero (or a release blocker exception policy specifically approved by security and product, excluding privacy/evidence integrity risks).

## 15. Deployment, recovery and maintainability

- [ ] **DEP-01** Frontend build, stateless FastAPI API, Postgres, Redis/Celery, workers, scheduler and object storage are provisioned in release-like staging.
- [ ] **DEP-02** API/worker environment and secrets are validated at startup; missing providers fail closed or show explicit unavailability.
- [ ] **DEP-03** Database migration execution is automated, repeatable and compatible with rolling/controlled deployment.
- [ ] **DEP-04** CI passes formatting, static/type checks, unit/integration/security tests and artifact builds.
- [ ] **DEP-05** One versioned release artifact/config set is deployed to staging and promoted without source drift.
- [ ] **DEP-06** Health/readiness checks cover API, queue/worker dependency state and persistent storage availability.
- [ ] **DEP-07** Fresh installation instructions work on a clean environment; a seeded sample investigation completes.
- [ ] **DEP-08** Rollback plan for API/worker changes and forward/backward database migrations is rehearsed.
- [ ] **DEP-09** Backup restore drill demonstrates usable data and authorized report/source references; RPO/RTO values are documented.
- [ ] **DEP-10** Incident runbook covers queue recovery, provider failure, index rebuild, leaked key and content-rights takedown.
- [ ] **DEP-11** Ownership and operational responsibility for deployed services are assigned before release.

## 16. Documentation, adoption and licenses

- [ ] **DOC-01** `README.md` accurately states current features, setup, supported modes and limitations.
- [ ] **DOC-02** BRD, SRS and `architecture.md` are reviewed against implementation and have version/status labels.
- [ ] **DOC-03** API reference/OpenAPI and TypeScript SDK examples are current and executable.
- [ ] **DOC-04** Adapter manifests describe real provider setup, health, quota, rights and fallback behavior.
- [ ] **DOC-05** Database schema, migration guide, backup/restore procedures and retention rules are documented.
- [ ] **DOC-06** Research/evidence model glossary explains relation labels, verdicts, provenance and calibration limits.
- [ ] **DOC-07** Evaluation protocol and benchmark results include dataset version, reviewer methodology and measured failures.
- [ ] **DOC-08** Contributor/developer setup, test execution and secure disclosure process are documented.
- [ ] **DOC-09** MIT project license and dependency/provider obligations are checked for consistency.
- [ ] **DOC-10** Demonstration script shows real three-class routing, highlighted passage, lineage, abstention/dispute and frozen export.

## 17. Pilot acceptance and release sign-off

- [ ] **REL-01** At least one campus/community target user group exercises a complete real-world investigation and provides recorded feedback.
- [ ] **REL-02** Pilot participants can locate the specific passage behind a report claim without developer assistance.
- [ ] **REL-03** Pilot demonstrates a disputed or insufficient-evidence finding without presenting a false truth claim.
- [ ] **REL-04** Pilot evidence shows whether results are useful, time-saving and correctable relative to a manual baseline.
- [ ] **REL-05** All material pilot defects are fixed, regression tested or classified as approved non-blocking limitations.
- [ ] **REL-06** Product owner signs BRD/MVP acceptance and scope compliance.
- [ ] **REL-07** Technical lead signs SRS/architecture, data migration, maintainability and recovery acceptance.
- [ ] **REL-08** Security/privacy reviewer signs tenant isolation, fetch security, retention and third-party rights acceptance.
- [ ] **REL-09** QA/research evaluator signs benchmark methodology, citation-support results and final regression report.
- [ ] **REL-10** Release manager records version/tag, deployed environment, release notes, evidence index and **GO** decision.

## 18. The hard release gates (all must be PASS)

| Gate | Pass condition | Result | Evidence / reviewer |
|---|---|---|---|
| G1: Scope | Required MVP functions delivered; exclusions declared | PENDING | |
| G2: Isolation | Zero known cross-tenant retrieval across database/search/cache/export | PENDING | |
| G3: Execution | Real multi-source dispatch + ≥3 executable source classes | PENDING | |
| G4: Reliability | Durable outbox, independent workers, retries, idempotency and cancellation proven | PENDING | |
| G5: Provenance | Immutable rights-permitted snapshots/passages and lineage inspectable | PENDING | |
| G6: Evidence | Claim/relationship/verdict semantics and abstention proven | PENDING | |
| G7: Citation integrity | 100% frozen citation resolution; human attribution benchmark meets approved targets | PENDING | |
| G8: Security/rights | No release-blocking SSRF, injection, privacy or copyright/retention findings | PENDING | |
| G9: User workflow | Real user completes inquiry, inspects evidence, reviews and exports frozen report | PENDING | |
| G10: Operations | Repeatable release, backups, rollback, telemetry and runbooks verified | PENDING | |
| G11: Quality | Benchmark, regression, resilience and cost evidence reviewed and approved | PENDING | |
| G12: Sign-off | Product, engineering, QA and security approvals documented | PENDING | |

> **Non-negotiable:** A failed gate is a **NO-GO**, regardless of the numerical checkbox completion percentage.

## 19. Completion evidence register (copy a row per verified item)

| Requirement ID | Status (`PASS`/`FAIL`/`N/A`) | Evidence link / build | Verified by | Date | Notes / N/A rationale |
|---|---|---|---|---|---|
| Example: RPT-03 | FAIL | `tests/reports/citation_integrity` | Unassigned | — | Must reach 100% frozen citation resolution |
|  |  |  |  |  |  |

### Suggested proof packages

- **Feature evidence:** merged PR, linked requirement ID, executable E2E result, screenshot/video of current release build.
- **Security evidence:** dated automated reports and signed manual review, with adversarial test coverage and remediation records.
- **Quality evidence:** frozen dataset, annotation protocol, confusion matrix, citation-support audit and failure analysis.
- **Deployment evidence:** release commit, migrations, rollback/restore drill, observability dashboard and runbook.
- **Business evidence:** recorded usability sessions, approved acceptance criteria and stakeholder decisions.

## 20. Recommended implementation-order tracker (not additional completion criteria)

| Phase | Priority work | Exit gate |
|---|---|---|
| 0 · Weeks 1–2 | Tenant scoping, misleading score removal, authorization/security tests | G2 and initial G8 |
| 1 · Weeks 3–4 | Real source router, adapter manifests, worker durability and coverage | G3, G4 |
| 2 · Weeks 5–8 | Snapshots, passages, claims, evidence relations, citation gate, inspector | G5, G6, G7 |
| 3 · Weeks 9–12 | Human benchmark, source-independence evaluation, pilot, monitors, release ops | G9, G10, G11, G12 |

Indicative windows are *planning targets*, not guaranteed delivery dates. Prioritize a passed exit gate over rushing to a later phase.

## 21. Deferred work: **not** required for v2 MVP 100%

Do not accidentally turn the MVP score into a never-ending backlog. Track these in separate future-release roadmaps instead of the mandatory denominator:

- [ ] **(O)** Split the modular monolith into independently deployed microservices **only after measured scaling or isolation pressure**.
- [ ] **(O)** Add Kafka, service mesh, multi-region operation or distributed sagas if required by actual production scale.
- [ ] **(O)** Add pgvector/OpenSearch or dedicated graph database only when retrieval/graph benchmarks justify them.
- [ ] **(O)** Enterprise SSO, proprietary enterprise data connectors, procurement features and certification programs.
- [ ] **(O)** Paid hosting plans, billing, advanced organizational administration and institution-only features.
- [ ] **(O)** Proprietary foundation model training, autonomous long-horizon agents and unbounded browsing.
- [ ] **(O)** Any probability-of-truth score **unless independently calibrated, validated and clearly communicated**.

## 22. Final declaration template

**Release identifier:** `________________`  
**Deployment / commit:** `________________`  
**Mandatory controls passed:** `_____ / _____ (____%)`  
**Release gates:** `_____ / 12 PASS`  
**Open blocking defects:** `_____`  
**Benchmark / report:** `________________`  
**Pilot acceptance evidence:** `________________`  
**Product owner:** `________________`  
**Engineering lead:** `________________`  
**Security reviewer:** `________________`  
**QA / evaluation lead:** `________________`  
**Decision / date:** `GO / NO-GO — ________________`

**Completion statement (use only after verification):** “CredenceAI 2.0 MVP is complete against the approved scope: every mandatory item is evidenced and passed, all twelve release gates pass, no release-blocking defects remain, and the required approvers have signed off.”

---

**Traceability references:** project definition §§5–16, 18–22 and Definition of Done; `architecture.md` §§2–end; corresponding BRD/SRS acceptance requirements. The original project proposal describes a target release, **not proof that these checklist items have been completed**.
