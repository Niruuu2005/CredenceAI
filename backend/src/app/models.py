import datetime
from sqlalchemy import Column, String, DateTime, Text, Float, ForeignKey, Integer, Boolean, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utc_now)


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    tenant = relationship("Tenant", backref="workspaces")


class Membership(Base):
    __tablename__ = "memberships"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), default="researcher", nullable=False)  # admin, researcher, reviewer, viewer
    created_at = Column(DateTime, default=utc_now)

    __table_args__ = (
        UniqueConstraint("user_id", "workspace_id", name="uq_user_workspace"),
    )

    user = relationship("User", backref="memberships")
    workspace = relationship("Workspace", backref="memberships")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(50), primary_key=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(String(50), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(50), nullable=False)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(50), primary_key=True)
    trace_id = Column(String(50), nullable=False, index=True)
    job_type = Column(String(50), nullable=False)
    input = Column(Text, nullable=False)
    vertical = Column(String(50), nullable=True)
    priority = Column(String(20), default="normal")
    routing_mode = Column(String(20), default="free_first")
    execution_mode = Column(String(20), default="standard")
    status = Column(String(20), default="queued")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)

    source_results = relationship("SourceResult", back_populates="job", cascade="all, delete-orphan")
    normalized_results = relationship("NormalizedResult", back_populates="job", cascade="all, delete-orphan")


class SourceResult(Base):
    __tablename__ = "source_results"

    id = Column(String(50), primary_key=True)
    job_id = Column(String(50), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    source = Column(String(50), nullable=False)
    source_type = Column(String(50), nullable=False)
    input_value = Column(Text, nullable=False)
    raw_payload_ref = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False)
    confidence = Column(Float, default=1.0)
    fetched_at = Column(DateTime, default=utc_now)
    schema_version = Column(String(10), default="v0.1")

    job = relationship("Job", back_populates="source_results")
    normalized_results = relationship("NormalizedResult", back_populates="source_result", cascade="all, delete-orphan")


class NormalizedResult(Base):
    __tablename__ = "normalized_results"

    id = Column(String(50), primary_key=True)
    job_id = Column(String(50), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    source_result_id = Column(String(50), ForeignKey("source_results.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    canonical_url = Column(Text, nullable=True)
    snippet = Column(Text, nullable=True)
    source = Column(String(50), nullable=False)
    language = Column(String(10), default="en")
    published_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=utc_now)
    raw_payload_ref = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    job = relationship("Job", back_populates="normalized_results")
    source_result = relationship("SourceResult", back_populates="normalized_results")
    
    # Version 0.2 additions
    quality_scores = relationship("QualityScore", back_populates="result", cascade="all, delete-orphan", uselist=False)
    dedup_members = relationship("DedupMember", back_populates="result", cascade="all, delete-orphan")
    entity_links = relationship("EntityLink", back_populates="result", cascade="all, delete-orphan")


class QualityScore(Base):
    __tablename__ = "quality_scores"

    id = Column(String(50), primary_key=True)
    result_id = Column(String(50), ForeignKey("normalized_results.id", ondelete="CASCADE"), nullable=False)
    relevance_score = Column(Float, default=0.0)
    source_reliability_score = Column(Float, default=0.0)
    freshness_score = Column(Float, default=0.0)
    authority_score = Column(Float, default=0.0)
    entity_match_score = Column(Float, default=0.0)
    dedup_confidence = Column(Float, default=0.0)
    extraction_likelihood_score = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    final_trust_score = Column(Float, default=0.0)
    decision = Column(String(50), default="accept")
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    result = relationship("NormalizedResult", back_populates="quality_scores")


class DedupGroup(Base):
    __tablename__ = "dedup_groups"

    id = Column(String(50), primary_key=True)
    group_type = Column(String(50), nullable=False)
    canonical_result_id = Column(String(50), nullable=True)
    canonical_url = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=True)
    simhash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    members = relationship("DedupMember", back_populates="group", cascade="all, delete-orphan")


class DedupMember(Base):
    __tablename__ = "dedup_members"

    id = Column(String(50), primary_key=True)
    group_id = Column(String(50), ForeignKey("dedup_groups.id", ondelete="CASCADE"), nullable=False)
    result_id = Column(String(50), ForeignKey("normalized_results.id", ondelete="CASCADE"), nullable=False)
    match_type = Column(String(50), nullable=False)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=utc_now)

    group = relationship("DedupGroup", back_populates="members")
    result = relationship("NormalizedResult", back_populates="dedup_members")


class Entity(Base):
    __tablename__ = "entities"

    id = Column(String(50), primary_key=True)
    canonical_name = Column(String(255), nullable=False)
    entity_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    official_url = Column(Text, nullable=True)
    wikidata_id = Column(String(50), nullable=True, index=True)
    wikipedia_url = Column(Text, nullable=True)
    openalex_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    aliases = relationship("EntityAlias", back_populates="entity", cascade="all, delete-orphan")
    links = relationship("EntityLink", back_populates="entity", cascade="all, delete-orphan")


class EntityAlias(Base):
    __tablename__ = "entity_aliases"

    id = Column(String(50), primary_key=True)
    entity_id = Column(String(50), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    alias = Column(String(255), nullable=False)
    language = Column(String(10), default="en")
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)
    source = Column(String(50), nullable=True)
    confidence = Column(Float, default=1.0)

    entity = relationship("Entity", back_populates="aliases")


class EntityLink(Base):
    __tablename__ = "entity_links"

    id = Column(String(50), primary_key=True)
    entity_id = Column(String(50), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    result_id = Column(String(50), ForeignKey("normalized_results.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String(50), nullable=True)
    mention = Column(String(255), nullable=True)
    confidence = Column(Float, default=1.0)
    decision = Column(String(50), default="accept")
    created_at = Column(DateTime, default=utc_now)

    entity = relationship("Entity", back_populates="links")
    result = relationship("NormalizedResult", back_populates="entity_links")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(50), primary_key=True)
    job_id = Column(String(50), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True)
    url = Column(Text, nullable=False)
    title = Column(String(255), nullable=True)
    body_text = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True, index=True)
    language = Column(String(10), default="en")
    extraction_quality_score = Column(Float, default=0.0)
    raw_payload_ref = Column(String(255), nullable=True)
    mime_type = Column(String(100), default="text/html")
    crawled_at = Column(DateTime, default=utc_now)

    job = relationship("Job")


class CrawlPolicyDecision(Base):
    __tablename__ = "crawl_policy_decisions"

    id = Column(String(50), primary_key=True)
    job_id = Column(String(50), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True)
    url = Column(Text, nullable=False)
    allowed = Column(Boolean, default=True)
    reason = Column(Text, nullable=True)
    checked_at = Column(DateTime, default=utc_now)

    job = relationship("Job")


class VerticalRun(Base):
    __tablename__ = "vertical_runs"

    id = Column(String(50), primary_key=True)
    pack_name = Column(String(50), nullable=False)
    query = Column(Text, nullable=False)
    status = Column(String(20), default="queued")
    created_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)
    report = Column(Text, nullable=True)  # JSON serialized
    error_message = Column(Text, nullable=True)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    owner = Column(String(100), nullable=False)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    label = Column(String(100), nullable=True)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)


class Monitor(Base):
    __tablename__ = "monitors"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    topic = Column(String(255), nullable=False)
    scope = Column(String(255), nullable=True)
    status = Column(String(20), default="Active")
    interval = Column(String(50), default="Daily")
    last_check = Column(String(50), default="Just created")
    health = Column(String(20), default="Green")
    created_at = Column(DateTime, default=utc_now)


class Collection(Base):
    __tablename__ = "collections"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    items_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class StripeEvent(Base):
    __tablename__ = "stripe_events"

    id = Column(String(100), primary_key=True)
    event_type = Column(String(100), nullable=False)
    processed_at = Column(DateTime, default=utc_now)


class User(Base):
    __tablename__ = "users"

    id = Column(String(50), primary_key=True)  # Google Sub ID or local mock ID
    email = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    picture = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    plan = Column(String(20), default="Free")  # "Free", "Pro", "Enterprise"
    search_quota_limit = Column(Integer, default=50)
    stripe_customer_id = Column(String(100), nullable=True, index=True)
    subscription_id = Column(String(100), nullable=True)
    subscription_status = Column(String(30), nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    role = Column(String(20), default="user")
    account_status = Column(String(20), default="active")
    usage_period_start = Column(DateTime, nullable=True)


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    min_citations = Column(Integer, default=2)
    scholarly_focus = Column(String(50), default="balanced")
    api_logging_enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class CollectionItem(Base):
    __tablename__ = "collection_items"

    id = Column(String(50), primary_key=True)
    collection_id = Column(String(50), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False, index=True)
    result_id = Column(String(50), nullable=True)
    title = Column(String(255), nullable=False)
    url = Column(Text, nullable=True)
    snippet = Column(Text, nullable=True)
    source = Column(String(50), nullable=True)
    job_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=utc_now)


class EnterpriseContact(Base):
    __tablename__ = "enterprise_contacts"

    id = Column(String(50), primary_key=True)
    email = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="new")
    created_at = Column(DateTime, default=utc_now)


class MonitorJob(Base):
    __tablename__ = "monitor_jobs"

    id = Column(String(50), primary_key=True)
    monitor_id = Column(String(50), ForeignKey("monitors.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(50), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now)


class AgentMemoryRecord(Base):
    __tablename__ = "agent_memory_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(String(50), index=True, nullable=False)
    agent_name = Column(String(100), nullable=False)
    step_index = Column(Integer, default=0)
    decision_json = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)


# ==============================================================================
# CredenceAI 2.0 Core Entities (DATA-01 to DATA-08)
# ==============================================================================

class ResearchRun(Base):
    """
    Durable research investigation run.
    Implements FR-002, FR-003, DATA-02.
    """
    __tablename__ = "research_runs"

    id = Column(String(50), primary_key=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(String(50), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    question = Column(Text, nullable=False)
    mode = Column(String(30), default="investigate", nullable=False)  # discover, investigate, deep_investigation
    status = Column(String(30), default="created", nullable=False, index=True)
    # created, queued, planning, retrieving, extracting, normalizing, verifying, reporting,
    # completed, partial, failed, cancelled, timed_out
    idempotency_key = Column(String(100), nullable=True, index=True)
    filters_json = Column(Text, nullable=True)
    budget_json = Column(Text, nullable=True)
    config_version = Column(String(20), default="v2.0", nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("workspace_id", "idempotency_key", name="uq_ws_run_idempotency"),
    )

    steps = relationship("RunStep", back_populates="run", cascade="all, delete-orphan", order_by="RunStep.created_at")


class RunStep(Base):
    """
    Individual stage step of a research run with idempotency and retry tracking.
    Implements FR-003, NFR-002, DATA-02.
    """
    __tablename__ = "run_steps"

    id = Column(String(50), primary_key=True)
    run_id = Column(String(50), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    step_key = Column(String(50), nullable=False)  # planning, retrieving, extracting, normalizing, verifying, reporting
    state = Column(String(30), default="pending", nullable=False)  # pending, running, completed, failed, cancelled, skipped
    input_version = Column(String(20), default="v1", nullable=False)
    attempt_count = Column(Integer, default=0, nullable=False)
    duration_ms = Column(Float, default=0.0)
    error_type = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("run_id", "step_key", "input_version", name="uq_run_step_idempotency"),
    )

    run = relationship("ResearchRun", back_populates="steps")


class OutboxEvent(Base):
    """
    Transactional outbox event record.
    Implements NFR-001, DATA-08.
    """
    __tablename__ = "outbox_events"

    id = Column(String(50), primary_key=True)
    aggregate_type = Column(String(50), nullable=False, index=True)  # e.g., "research_run"
    aggregate_id = Column(String(50), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)  # e.g., "run.created", "run.step_completed"
    payload_json = Column(Text, nullable=False)
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, dispatched, failed
    retry_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    processed_at = Column(DateTime, nullable=True)


class Source(Base):
    """
    Canonical source entity preserving publisher and syndication lineage.
    Implements FR-007, FR-011, DATA-03.
    """
    __tablename__ = "sources"

    id = Column(String(50), primary_key=True)
    canonical_url = Column(Text, nullable=False, index=True)
    publisher = Column(String(255), nullable=True)
    source_class = Column(String(50), default="web", nullable=False)
    syndication_upstream_id = Column(String(50), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    rights_metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)


class Snapshot(Base):
    """
    Immutable content snapshot or rights-permitted excerpt.
    Implements FR-008, DATA-04.
    """
    __tablename__ = "snapshots"

    id = Column(String(50), primary_key=True)
    source_id = Column(String(50), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    content_hash = Column(String(64), nullable=False, index=True)  # SHA-256 of text
    storage_ref = Column(String(255), nullable=True)  # S3 URI if full-text stored
    permitted_excerpt = Column(Text, nullable=True)  # Excerpt when full retention disallowed
    rights_status = Column(String(50), default="fair_use_excerpt", nullable=False)
    fetched_at = Column(DateTime, default=utc_now, nullable=False)

    passages = relationship("Passage", back_populates="snapshot", cascade="all, delete-orphan")


class Passage(Base):
    """
    Inspectable passage with stable offset anchors and hash.
    Implements FR-008, DATA-04.
    """
    __tablename__ = "passages"

    id = Column(String(50), primary_key=True)
    snapshot_id = Column(String(50), ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    text_content = Column(Text, nullable=False)
    char_offset_start = Column(Integer, default=0, nullable=False)
    char_offset_end = Column(Integer, default=0, nullable=False)
    passage_hash = Column(String(64), nullable=False, index=True)
    extraction_version = Column(String(20), default="v1.0", nullable=False)
    created_at = Column(DateTime, default=utc_now)

    snapshot = relationship("Snapshot", back_populates="passages")


class Claim(Base):
    """
    Atomic factual proposition with explicit scope.
    Implements FR-009, DATA-05.
    """
    __tablename__ = "claims"

    id = Column(String(50), primary_key=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    proposition = Column(Text, nullable=False)
    subject = Column(String(255), nullable=True)
    predicate = Column(String(255), nullable=True)
    object_val = Column(Text, nullable=True)
    units = Column(String(50), nullable=True)
    temporal_scope = Column(String(100), nullable=True)
    geographic_scope = Column(String(100), nullable=True)
    origin_type = Column(String(50), default="user_submitted", nullable=False)  # user_submitted, source_extracted
    extractor_version = Column(String(20), default="v1.0", nullable=False)
    created_at = Column(DateTime, default=utc_now)


class ClaimEvidence(Base):
    """
    Grounding edge between an atomic claim and an inspectable passage.
    Implements FR-010, DATA-05, EVD-05.
    """
    __tablename__ = "claim_evidence"

    id = Column(String(50), primary_key=True)
    claim_id = Column(String(50), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    passage_id = Column(String(50), ForeignKey("passages.id", ondelete="CASCADE"), nullable=False, index=True)
    relation = Column(String(30), nullable=False)  # supports, contradicts, mentions, irrelevant, uncertain
    rationale = Column(Text, nullable=True)
    assessor_version = Column(String(20), default="v1.0", nullable=False)
    reviewer_id = Column(String(50), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)


class ClaimVerdict(Base):
    """
    Run-scoped verdict on an assessed claim.
    Implements FR-012, DATA-06, EVD-10.
    """
    __tablename__ = "claim_verdicts"

    id = Column(String(50), primary_key=True)
    run_id = Column(String(50), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_id = Column(String(50), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    verdict = Column(String(30), nullable=False)  # supported, disputed, insufficient_evidence, not_assessed
    rationale = Column(Text, nullable=True)
    evaluator_version = Column(String(20), default="v2.0", nullable=False)
    created_at = Column(DateTime, default=utc_now)


class Report(Base):
    """
    Citation-frozen reproducible research brief.
    Implements FR-015, FR-016, DATA-07, Gate G7.
    """
    __tablename__ = "reports"

    id = Column(String(50), primary_key=True)
    run_id = Column(String(50), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    title = Column(String(255), nullable=False)
    body_markdown = Column(Text, nullable=False)
    manifest_hash = Column(String(64), nullable=False)  # SHA-256 of frozen passage citations
    status = Column(String(30), default="draft", nullable=False)  # draft, approved, frozen
    reviewed_by = Column(String(50), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


