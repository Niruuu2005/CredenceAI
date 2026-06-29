import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field, model_validator

class JobCreate(BaseModel):
    job_type: str = Field(default="search_query", description="Type of job (e.g. search_query)")
    input: Optional[str] = Field(default=None, description="Query or input content")
    query: Optional[str] = Field(default=None, description="SDK search query")
    vertical: Optional[str] = Field(default="web", description="Target vertical")
    priority: Optional[str] = Field(default="normal", description="Priority level")
    routing_mode: Optional[str] = Field(default="free_first", description="Routing mode")
    execution_mode: Optional[str] = Field(default="standard", description="Execution mode")
    
    # SDK fields
    mode: Optional[str] = Field(default="standard", description="SDK latency mode")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Passthrough metadata")
    intent: Optional[str] = Field(default=None, description="SDK intent")

    @model_validator(mode="before")
    @classmethod
    def check_input_or_query(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "input" not in data and "query" not in data:
                raise ValueError("Either 'input' or 'query' must be provided.")
        return data

# Alias for SDK compatibility
CreateJobRequest = JobCreate

class JobSubmitResponse(BaseModel):
    job_id: str
    trace_id: str
    status: str
    created_at: datetime.datetime

class QualitySummary(BaseModel):
    accepted: int = 0
    rejected: int = 0
    manual_review: int = 0

class ErrorResponse(BaseModel):
    error: str        # machine-readable error code
    message: str      # human-readable message
    trace_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    results_count: int
    failed_events: int
    quality_summary: QualitySummary
    created_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None
    error_message: Optional[str] = None
    job_type: Optional[str] = None
    input: Optional[str] = None
    submitted_at: Optional[datetime.datetime] = None
    # SDK compatibility fields
    result: Optional[Dict[str, Any]] = None
    error: Optional[ErrorResponse] = None
    trace_id: Optional[str] = None

class JobResponse(BaseModel):
    job_id: str
    status: str           # "queued" | "running" | "completed" | "failed"
    result: Optional[Dict[str, Any]] = None
    error: Optional[ErrorResponse] = None
    trace_id: Optional[str] = None
    created_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None

class ApiKeyCreateRequest(BaseModel):
    owner: str
    label: Optional[str] = None

class ApiKeyCreateResponse(BaseModel):
    key: str          # raw key — returned once only
    owner: str
    label: Optional[str] = None
    created_at: datetime.datetime

class SearchResultItem(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    snippet: Optional[str] = None
    source: Optional[str] = None
    score: Optional[float] = None
    document: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    total: Optional[int] = None
    trace_id: Optional[str] = None

class CitationSchema(BaseModel):
    citation_id: int
    title: str
    url: str
    source: str

class SynthesisResponse(BaseModel):
    summary: str
    citations: Dict[int, CitationSchema]
    confidence_score: float

class ExportRequest(BaseModel):
    format: str = Field(default="json", description="Export format (json or csv)")

class ExportResponse(BaseModel):
    format: str
    content: str


# --- Version 0.5 New Schemas ---

class DuplicateResponse(BaseModel):
    id: str
    title: str
    url: str
    snippet: Optional[str] = None
    source: str
    match_type: str
    confidence: float

class EntityResponse(BaseModel):
    id: str
    canonical_name: str
    entity_type: Optional[str] = None
    description: Optional[str] = None
    wikidata_id: Optional[str] = None
    wikipedia_url: Optional[str] = None
    confidence: float
    mention: Optional[str] = None

class QualityScoreResponse(BaseModel):
    relevance_score: float
    source_reliability_score: float
    freshness_score: float
    authority_score: float
    entity_match_score: float
    dedup_confidence: float
    extraction_likelihood_score: float
    risk_score: float
    final_trust_score: float
    decision: str
    reason: Optional[str] = None

class NormalizedResultResponse(BaseModel):
    id: str
    job_id: str
    source_result_id: str
    title: str
    url: str
    canonical_url: Optional[str] = None
    snippet: Optional[str] = None
    source: str
    language: str
    published_at: Optional[datetime.datetime] = None
    fetched_at: datetime.datetime
    created_at: datetime.datetime
    quality_scores: Optional[QualityScoreResponse] = None
    duplicates: List[DuplicateResponse] = []
    entities: List[EntityResponse] = []

class AgentDecisionResponse(BaseModel):
    id: int
    job_id: str
    agent_name: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    reasoning: Optional[str] = None
    confidence_score: float
    timestamp: datetime.datetime
    execution_time_ms: Optional[int] = None
    success: bool
    error_message: Optional[str] = None

class DecisionStatsResponse(BaseModel):
    total_decisions: int
    successful: int
    failed: int
    success_rate: float
    avg_confidence: float
    avg_execution_time_ms: float
    agents_used: List[str]

class SystemMetricsResponse(BaseModel):
    status: str
    jobs_count: int
    results_count: int
    accepted_count: int
    review_count: int
    rejected_count: int
    agent_decision_stats: DecisionStatsResponse

class VerticalPackInfo(BaseModel):
    name: str
    description: str
    enabled: bool

class VerticalRunResponse(BaseModel):
    run_id: str
    pack_name: str
    query: str
    status: str
    created_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None
    report: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class VerticalRunCreate(BaseModel):
    query: str
    config: Optional[Dict[str, Any]] = None

class EvidenceClaimResponse(BaseModel):
    claim_id: str
    text: str
    entity: str
    claim_type: str
    source_url: str
    source_reliability: float
    extracted_at: str

class ClaimNodeResponse(BaseModel):
    node_id: str
    canonical_text: str
    entity: str
    corroboration_count: int
    contradiction_count: int
    supporting_sources: List[str]
    contradicting_sources: List[str]
    avg_source_reliability: float
    confidence: float
    claim_type: str

class ClaimEdgeResponse(BaseModel):
    from_node: str = Field(alias="from")
    to_node: str = Field(alias="to")
    relationship: str
    weight: float

    model_config = {"populate_by_name": True}

class EvidenceGraphResponse(BaseModel):
    nodes: List[ClaimNodeResponse]
    edges: List[ClaimEdgeResponse]
    summary: Dict[str, Any]

class FactResponse(BaseModel):
    claim: str
    confidence: float
    corroboration: int
    sources: List[str]

class ContradictionResponse(BaseModel):
    claim: str
    sources: List[str]

class IntelligenceCardResponse(BaseModel):
    entity_name: str
    entity_type: str
    canonical_name: str
    wikidata_qid: Optional[str] = None
    description: Optional[str] = None
    key_facts: List[FactResponse]
    contradictions: List[ContradictionResponse]
    related_entities: List[str]
    source_count: int
    avg_confidence: float
    highest_corroboration: int
    sources: List[str]
    generated_at: str
    vertical: str
    freshness_label: str


# --- API Key, Monitor, and Collection Integration Schemas ---

class ApiKeyResponse(BaseModel):
    id: int
    owner: str
    label: Optional[str] = None
    revoked: bool
    created_at: datetime.datetime
    last_used_at: Optional[datetime.datetime] = None

    model_config = {"from_attributes": True}


class MonitorCreate(BaseModel):
    topic: str
    scope: Optional[str] = "Web & News Indexes"
    interval: Optional[str] = "Daily"


class MonitorResponse(BaseModel):
    id: str
    topic: str
    scope: str
    status: str
    interval: str
    last_check: str
    health: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CollectionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    items_count: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}



