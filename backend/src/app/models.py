import datetime
from sqlalchemy import Column, String, DateTime, Text, Float, ForeignKey, Integer, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

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
    label = Column(String(100), nullable=True)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)


class Monitor(Base):
    __tablename__ = "monitors"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
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




