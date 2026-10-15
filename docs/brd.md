Business case, outcomes, stakeholders, scope and acceptance for an evidence-first research platform.

| Project | CredenceAI 2.0                                        |
|---------|-------------------------------------------------------|
| Status  | Proposed requirements; subject to review and approval |
| Basis   | CredenceAI project definition v2.0, 14 October 2026   |

# 1. Executive overview

CredenceAI 2.0 is a proposed evolution of an open-source research platform. It helps users discover relevant material, inspect the exact passages underpinning factual assessments, distinguish independent from repeated reporting, and export auditable briefs. Its core promise is evidence traceability, not automated determination of universal truth.

# 2. Business problem and opportunity

- Discovery friction: public, news, scholarly and structured material is fragmented across services.

- Evidence ambiguity: relevance or publisher authority can be mistaken for actual support of a specific claim.

- Provenance loss: a cited link may not preserve the passage, timestamp or source context needed for audit.

- Access inequality: small research teams need affordable, transparent alternatives to high-touch proprietary tools.

Business opportunity: provide a free-first, self-hostable workflow converting retrieved sources into inspectable evidence and reproducible research outcomes.

# 2.1 Unique Selling Proposition (USP) & Competitive Positioning

CredenceAI occupies a distinct tier between raw web search engines, conversational generative AI chat, and proprietary research tools:

| Platform Class | Representative Tools | Primary Limitation | CredenceAI Differentiation |
|---|---|---|---|
| **Raw Search Engines** | Google, Bing, DuckDuckGo | Returns millions of unranked URLs without synthesizing factual validity; ads/SEO manipulation. | Converts multi-source hits into atomic propositions with passage-level evidence relations. |
| **Conversational Generative AI** | Perplexity AI, ChatGPT Search | Generates fluent text with plausible links; frequently hallucinate citations or conflate repetition with truth. | **Eliminates probability theater:** 100% frozen citations, cryptographic hashes, typed relations (`supports`/`refutes`). |
| **Academic Literature Search** | Consensus, Semantic Scholar | Restricted purely to scientific papers; lacks web, civic data, news wire, or corporate filing integration. | Cross-domain integration (Wikidata, Wikipedia, Crossref, OpenAlex, Common Crawl, GDELT, regulatory filings). |
| **Proprietary Risk Intelligence** | Bloomberg, LexisNexis, Factiva | Prohibitively expensive ($20k+/yr); closed black-box models inaccessible to community fact-checkers. | Free-first, 100% open-source, modular monolith deployable on standard free-tier cloud stacks. |

# 3. Objectives and expected value

| ID    | Business objective                                       | Success indication                                                        |
|-------|----------------------------------------------------------|---------------------------------------------------------------------------|
| BO-01 | Reduce manual effort to produce an evidence-backed brief | Measured time-to-brief versus manual baseline                             |
| BO-02 | Make findings independently auditable                    | Human-reviewed proportion of material statements with supporting passages |
| BO-03 | Expose uncertainty and disagreement                      | Coverage gaps, disputes and abstentions visible to users                  |
| BO-04 | Make small-team adoption practical                       | Pilot completion and repeat use among student/community teams             |
| BO-05 | Control trust, legal and operational risks               | Tenant isolation, permitted retention, bounded run costs                  |

# 4. Stakeholders, Personas & Public Impact Use Cases

## 4.1 Stakeholder Personas

| Stakeholder | Primary Need | Real-World Value |
|---|---|---|
| **Student Researchers** | Cited brief, papers, limitations and reproducible investigations | Eliminates citation fabrication in academic projects |
| **Campus & Community Fact-Checkers** | Claim-to-passage support, contradiction mapping, and reviewer audit | Streamlines verification of local news & social media rumors |
| **Small Newsrooms & Independent Journalists** | Source dates, wire lineage, and syndication detection | Distinguishes original reporting from syndicated wire copy |
| **Public Policy NGOs & Civic Watchdogs** | Shareable policy investigations and continuous monitoring | Tracks legislative statements and budget allocations over time |
| **Developers & Risk Analysts** | Typed API/SDK and structured evidence export | Integrates verified grounding into internal decision pipelines |
| **Workspace Administrators** | Multi-tenant membership, quotas, and retention policies | Enforces strict data isolation and budget governance |

## 4.2 Rural and Urban Public Impact Domains

1. **Rural Agriculture & Food Security:**
   - *Subsidy & Yield Claims:* Audit claims regarding drought-resistant seeds, localized rainfall statistics, and government fertilizer subsidy allocations.
   - *Price Gouging & Market Rumors:* Verify regional commodity prices against mandi/wholesale market registries to protect smallholder farmers from predatory middlemen.
2. **Rural & Community Healthcare:**
   - *Public Health Rumors:* Rapidly audit viral health rumors (e.g., unauthorized remedies, contaminated water sources) against peer-reviewed WHO and PubMed literature.
   - *Clinic Funding Verification:* Cross-reference stated government health center allocations with physical procurement and public expenditure records.
3. **Urban Civic Governance & Municipal Transparency:**
   - *Infrastructure Appropriations:* Audit municipal statements on road construction, flood defense projects, and public transit funding against published audit reports.
   - *Zoning & Land Use Disputes:* Verify industrial permit claims against regional environmental regulatory registries.
4. **Corporate Integrity & Environmental Accountability:**
   - *Greenwashing Audits:* Contrast corporate ESG disclosures (e.g., "carbon-neutral operations by 2024") with independent satellite telemetry, emissions data, and SEC filings.

# 5. Business scope

## 5.1 In scope for v2 MVP

- Discover, Investigate and Deep Investigation workflows, with existing monitor functionality extended for reproducible reruns.

- Multi-source discovery with visible provider execution, coverage and failure reporting.

- Stable source provenance, permitted content snapshots/excerpts, atomic claims and passage-level evidence relations.

- Scoped evidence verdicts: supported, disputed, insufficient_evidence and not_assessed.

- Human evidence inspection/review, collections, versioned citation-validated reports and basic export.

- Workspace/tenant isolation, bounded execution budgets, operational and quality measurement.

## 5.2 Explicitly out of scope

- Universal true/false judgments, unbounded autonomous browsing or long-horizon agents.

- Enterprise connectors, SSO, certification claims and paid search dependencies for the default experience.

- Proprietary foundation model training, premature microservices, Kafka or a dedicated graph database.

# 6. Business requirements

| ID    | Requirement                                                                                 | Priority |
|-------|---------------------------------------------------------------------------------------------|----------|
| BR-01 | Users shall initiate a scoped research task and select a research mode.                     | Must     |
| BR-02 | Users shall see which source classes ran, failed or were unavailable.                       | Must     |
| BR-03 | Users shall trace any material report assertion to permitted, inspectable source passages.  | Must     |
| BR-04 | The product shall distinguish support, contradiction, mention, irrelevance and uncertainty. | Must     |
| BR-05 | The product shall avoid expressing rankings as probabilities of factual truth.              | Must     |
| BR-06 | Reviewers shall annotate assessments without altering immutable source evidence.            | Must     |
| BR-07 | Users shall export versioned briefs preserving caveats and source provenance.               | Must     |
| BR-08 | Private workspaces, reports, search and cache shall be access-isolated.                     | Must     |
| BR-09 | Monitoring shall retain comparison history for configured reruns.                           | Should   |
| BR-10 | The free-first deployment shall remain viable with executable public adapters.              | Must     |
| BR-11 | Each run shall enforce explicit time, source, page, byte and model budgets.                 | Must     |
| BR-12 | Teams shall evaluate usefulness and evidence quality through human-labeled pilots.          | Must     |

# 7. Representative business process

A campus research team submits a scoped public-policy claim, chooses Investigate, reviews sources and highlighted passages, considers contradictions and source independence, records human notes, then exports a frozen brief with supporting evidence and stated limitations. Scheduled reruns can later identify changed evidence.

# 8. Value metrics and proposed release gates

| Metric                      | Proposed target / approach                                                           |
|-----------------------------|--------------------------------------------------------------------------------------|
| North-star                  | Share of completed tasks producing useful, human-reviewed, evidence-traceable briefs |
| Citation resolution         | 100% of report citations resolve to authorized frozen passage IDs                    |
| Passage support             | At least 95% supported statements in held-out human review                           |
| Unsupported material claims | At most 5% in initially reviewed generated reports                                   |
| Cross-tenant protection     | Zero known unauthorized retrieval in adversarial tests                               |
| Pilot value                 | Compare time-to-brief, user corrections and repeat usage against manual workflow     |
| Business economics          | Measure cost per completed run, adapter availability and source coverage             |

Targets above are proposed acceptance thresholds from the project definition, not measured outcomes.

# 8.1 Commercial Sustainability & Subscription Model

CredenceAI follows a sustainable open-core model designed to ensure indefinite free access for student researchers and community newsrooms while monetizing high-volume organizational workflows:

| Tier | Target Persona | Monthly Price | Quotas & Capabilities |
|---|---|---|---|
| **Community Free** | Student researchers, independent fact-checkers, civic watchdogs | **$0 / mo** | 50 research queries/day, 5 active monitors, 10 collections, standard public adapters, community Discord support. |
| **Research Pro** | Professional journalists, boutique investigative firms | **$29 / mo** | 500 research queries/day, unlimited monitors, automated scheduled runs, PDF/JSON export, priority worker dispatch. |
| **Institutional / NGO** | University labs, large newsrooms, international NGOs | **Custom / Annual** | Dedicated tenant isolation, custom source adapter integrations, SLA guarantees, on-premises / VPC deployment. |

**Stripe Billing Integration:**
- Production subscriptions are managed via Stripe Checkout and Customer Portal (`/api/billing/*`).
- Idempotent webhook handling synchronizes user subscription state, tier upgrades, and grace periods.
- Free-tier accounts do not require credit card entry.

# 9. Dependencies, assumptions and constraints

- Provider executability, credentials, health, usage quotas and license/robots rules vary at runtime.

- Full-text retention is limited by source rights; some evidence must be referenced through permitted excerpts.

- A research result may be partial or inconclusive; honest abstention is a successful product behavior.

- The existing FastAPI, React, TypeScript SDK and data assets are evolved incrementally with v1 compatibility.

- PostgreSQL, durable queue workers and object storage are proposed infrastructure components.

# 10. Business risks and response

| Risk                                     | Response                                                     |
|------------------------------------------|--------------------------------------------------------------|
| Misleading citation or conclusion        | Passage validation, reviewer workflow and uncertainty labels |
| Tenant data leakage                      | Mandatory authorization scopes and adversarial testing       |
| Repeated coverage counted as independent | Publisher/syndication lineage grouping                       |
| Provider outage or cost spikes           | Health-aware routing, capped budgets and partial reports     |
| Copyright/unsafe acquisition             | Rights-aware retention, robots rules and SSRF controls       |
| Low adoption / feature sprawl            | Narrow launch audience, task-based pilots and staged gates   |

# 11. Delivery and governance

| Phase                | Indicative timing | Business exit condition                                                                 |
|----------------------|-------------------|-----------------------------------------------------------------------------------------|
| 0\. Secure claims    | Weeks 1–2         | No known tested cross-tenant retrieval; no false verified labels                        |
| 1\. Real retrieval   | Weeks 3–4         | Three executable source classes observed in suitable integration tests                  |
| 2\. Passage MVP      | Weeks 5–8         | Every material report claim supported by an inspectable passage or explicit uncertainty |
| 3\. Pilot evaluation | Weeks 9–12        | Evidence quality, economics and task value measured in pilots                           |

Timing is indicative, not a delivery commitment. Scope expansion requires completion of phase exit criteria.

# 12. Approval and open decisions

- Confirm executive sponsor, product owner, technical owner and pilot-review approvers.

- Approve release gates and benchmark annotation procedure.

- Define permitted source classes, retention schedule, hosting limits and review escalation policy.

- Validate willingness to pay before committing to organizational hosting/pricing.

# 13. Source and document control

Primary source: CredenceAI, “Project definition, product requirements, and architecture specification,” proposed v2.0, updated 14 October 2026. This BRD restructures the business intent and does not assert that target features have shipped.
