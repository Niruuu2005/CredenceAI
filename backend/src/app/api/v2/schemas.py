"""
Pydantic Schemas for CredenceAI 2.0 API (v2).
Implements typed contracts for Research Runs, Claims, Evidence, and Frozen Reports.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class RunStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    step_key: str
    state: str
    attempt_count: int
    duration_ms: float
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ResearchRunCreateRequest(BaseModel):
    question: str = Field(..., min_length=3, description="Core inquiry proposition or question")
    mode: str = Field("investigate", description="Mode: discover, investigate, deep_investigation")
    idempotency_key: Optional[str] = Field(None, description="Client idempotency key for safe retries")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    budget: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ResearchRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    question: str
    mode: str
    status: str
    config_version: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    steps: List[RunStepResponse] = Field(default_factory=list)


class SourceItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    canonical_url: str
    publisher: Optional[str] = None
    source_class: str
    syndication_upstream_id: Optional[str] = None


class ClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    proposition: str
    subject: Optional[str] = None
    predicate: Optional[str] = None
    object_val: Optional[str] = None
    units: Optional[str] = None
    temporal_scope: Optional[str] = None
    geographic_scope: Optional[str] = None
    origin_type: str
    verdict: Optional[str] = None
    rationale: Optional[str] = None


class EvidenceEdgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    claim_id: str
    passage_id: str
    relation: str
    rationale: Optional[str] = None
    assessor_version: str
    passage_text: str
    publisher: Optional[str] = None
    canonical_url: Optional[str] = None
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    workspace_id: str
    version: int
    title: str
    body_markdown: str
    manifest_hash: str
    status: str
    reviewed_by: Optional[str] = None
    reviewer_notes: Optional[str] = None
    created_at: datetime


class EvidenceReviewRequest(BaseModel):
    new_relation: Optional[str] = Field(None, description="supports, contradicts, mentions, irrelevant, uncertain")
    reviewer_notes: Optional[str] = Field(None, description="Audited rationale for relationship classification")


class ReportApprovalRequest(BaseModel):
    reviewer_notes: Optional[str] = Field(None, description="Audited sign-off notes")


class MonitorCreateRequest(BaseModel):
    topic: str
    scope: Optional[str] = None
    interval: str = "Daily"


class MonitorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: Optional[str] = None
    topic: str
    scope: Optional[str] = None
    status: str
    interval: str
    health: str
    created_at: datetime


class MonitorDeltaResponse(BaseModel):
    monitor_id: str
    deltas_count: int
    summary: str
    detected_at: datetime
