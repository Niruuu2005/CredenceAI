"""Pydantic schemas for AgentGate API."""

from typing import Any, Literal

from pydantic import BaseModel, Field


StatusType = Literal["ready", "needs_clarification", "unsafe", "incomplete"]
RiskLevel = Literal["low", "medium", "high"]


class EvaluateTaskRequest(BaseModel):
    task_description: str = Field(..., min_length=1)
    goal: str | None = None
    available_context: dict[str, Any] = Field(default_factory=dict)
    proposed_action: str | None = None
    constraints: list[str] = Field(default_factory=list)


class EvaluateTaskResponse(BaseModel):
    status: StatusType
    risk_level: RiskLevel
    missing_info: list[str]
    recommended_next_action: str
    reasoning_summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    agent_instruction: str


class OptionItem(BaseModel):
    id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    action: str | None = None
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    estimated_risk: RiskLevel = "low"


class CompareOptionsRequest(BaseModel):
    decision_goal: str = Field(..., min_length=1)
    options: list[OptionItem] = Field(..., min_length=2, max_length=5)
    context: dict[str, Any] = Field(default_factory=dict)


class CompareOptionsResponse(BaseModel):
    recommended_option_id: str
    ranking: list[str]
    risk_level: RiskLevel
    reasoning_summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    agent_instruction: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    llm_mode: str
