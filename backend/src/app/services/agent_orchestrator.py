"""
Agent Orchestrator — multi-step agent loop with replanning and tool routing.

Implements the agentic pipeline per docs/archive/specs/20_AGENTIC_AI_LAYER.md.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.agents.base import AgentInput
from app.agents.source_selection_agent import SourceSelectionAgent
from app.agents.quality_critic_agent import QualityCriticAgent
from app.agents.entity_resolution_agent import EntityResolutionAgent
from app.agents.extraction_validation_agent import ExtractionValidationAgent
from app.agents.crawl_strategy_agent import CrawlStrategyAgent
from app.agents.experiment_agent import ExperimentAgent
from app.agents.ops_recovery_agent import OpsRecoveryAgent
from app.agents.planner_agent import PlannerAgent
from app.config import settings
from app.services.agent_runner import run_agent
from app.services.agent_working_memory import AgentWorkingMemory
from app.services.health_router import HealthRouter
from app.services.llm_client import LLMClient, AGENT_TOOLS

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Coordinates multi-agent execution with budget, memory, and replanning."""

    def __init__(self, db: Session):
        self.db = db
        self.memory = AgentWorkingMemory(db)
        self.max_iterations = settings.AGENT_MAX_ITERATIONS

    async def run_pipeline(
        self,
        job_id: str,
        query: str,
        vertical: str,
        mode: str = "standard",
        normalized_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Execute the full agentic pipeline for a job."""
        if not settings.ENABLE_AGENTIC_PIPELINE:
            return {"skipped": True, "reason": "agentic pipeline disabled"}

        context: Dict[str, Any] = {
            "query": query,
            "vertical": vertical,
            "mode": mode,
            "iteration": 0,
        }
        pipeline_result: Dict[str, Any] = {
            "source_selection": None,
            "quality_critique": None,
            "entity_resolution": None,
            "crawl_strategies": None,
            "extraction_validation": None,
            "ops_recovery": None,
            "replan": None,
        }

        # Step 0: Ops health check
        health_router = HealthRouter()
        health_status = health_router.get_provider_health()
        ops_decision = await run_agent(
            self.db,
            OpsRecoveryAgent(),
            AgentInput(
                context={"health_status": health_status},
                job_id=job_id,
                user_request=query,
            ),
        )
        pipeline_result["ops_recovery"] = ops_decision.output_data
        if ops_decision.success and ops_decision.output_data:
            recovery = ops_decision.output_data.get("decision", {})
            if recovery.get("status") == "degraded":
                context["provider_fallbacks"] = recovery.get("actions", [])

        for iteration in range(self.max_iterations):
            context["iteration"] = iteration

            # Step 1: Source selection
            src_decision = await run_agent(
                self.db,
                SourceSelectionAgent(),
                AgentInput(
                    context={
                        "query": query,
                        "vertical": vertical,
                        "max_sources": settings.DEFAULT_MAX_SOURCES,
                    },
                    job_id=job_id,
                    user_request=query,
                ),
            )
            if src_decision.success and src_decision.output_data:
                sel = src_decision.output_data.get("decision", {})
                pipeline_result["source_selection"] = sel
                selected = sel.get("selected_sources", [])
                if selected:
                    context["selected_sources"] = selected

            # Step 2: Quality critic (borderline results only)
            if normalized_results:
                borderline = [
                    r for r in normalized_results
                    if r.get("quality_scores", {}).get("decision") == "manual_review"
                    or 0.4 <= r.get("quality_scores", {}).get("final_trust_score", 0) < 0.7
                ]
                if borderline:
                    docs = [
                        {
                            "url": r.get("url", ""),
                            "title": r.get("title", ""),
                            "text": r.get("snippet", ""),
                            "source_name": r.get("source", "unknown"),
                        }
                        for r in borderline
                    ]
                    qc_decision = await run_agent(
                        self.db,
                        QualityCriticAgent(),
                        AgentInput(
                            context={"query": query, "documents": docs},
                            job_id=job_id,
                            user_request=query,
                        ),
                    )
                    if qc_decision.success:
                        pipeline_result["quality_critique"] = qc_decision.output_data
                        self._apply_quality_critique(normalized_results, qc_decision.output_data)

            # Step 3: Entity resolution for ambiguous entities
            entities = self._extract_entity_candidates(query, normalized_results)
            if entities:
                er_decision = await run_agent(
                    self.db,
                    EntityResolutionAgent(),
                    AgentInput(
                        context={
                            "mention": entities[0],
                            "context_text": query,
                            "candidates": entities,
                        },
                        job_id=job_id,
                        user_request=query,
                    ),
                )
                if er_decision.success:
                    pipeline_result["entity_resolution"] = er_decision.output_data

            # Step 4: Crawl strategy (deep mode)
            if mode == "deep" and normalized_results:
                accepted = [
                    r for r in normalized_results
                    if r.get("quality_scores", {}).get("decision") == "accept"
                ]
                urls = [r["url"] for r in accepted[:5] if r.get("url")]
                trust = {r["url"]: r.get("quality_scores", {}).get("final_trust_score", 0.5) for r in accepted if r.get("url")}
                if urls:
                    cs_decision = await run_agent(
                        self.db,
                        CrawlStrategyAgent(),
                        AgentInput(
                            context={"urls": urls, "trust_scores": trust},
                            job_id=job_id,
                            user_request=query,
                        ),
                    )
                    if cs_decision.success:
                        pipeline_result["crawl_strategies"] = cs_decision.output_data

            # Step 5: Extraction validation placeholder for crawled content
            if normalized_results:
                ev_decision = await run_agent(
                    self.db,
                    ExtractionValidationAgent(),
                    AgentInput(
                        context={
                            "url": normalized_results[0].get("url", ""),
                            "extracted_text": normalized_results[0].get("snippet", ""),
                            "title": normalized_results[0].get("title", ""),
                        },
                        job_id=job_id,
                        user_request=query,
                    ),
                )
                if ev_decision.success:
                    pipeline_result["extraction_validation"] = ev_decision.output_data

            # Step 6: Replan check via LLM tool routing
            should_replan = await self._check_replan(job_id, query, context, normalized_results)
            if not should_replan:
                break

            replan_decision = await run_agent(
                self.db,
                PlannerAgent(),
                AgentInput(
                    context={"user_goal": f"Refine search for: {query}"},
                    job_id=job_id,
                    user_request=query,
                ),
                estimated_tokens=800,
            )
            pipeline_result["replan"] = replan_decision.output_data
            if replan_decision.success and replan_decision.output_data:
                plan = replan_decision.output_data.get("decision", {})
                new_verticals = plan.get("recommended_verticals", [])
                if new_verticals:
                    vertical = new_verticals[0]
                    context["vertical"] = vertical

        pipeline_result["memory"] = self.memory.get_context(job_id)
        return pipeline_result

    async def _check_replan(
        self,
        job_id: str,
        query: str,
        context: Dict[str, Any],
        results: Optional[List[Dict[str, Any]]],
    ) -> bool:
        """Use LLM tool routing to decide if replanning is needed."""
        if context.get("iteration", 0) >= self.max_iterations - 1:
            return False
        if not results:
            return True
        accepted = sum(
            1 for r in results
            if r.get("quality_scores", {}).get("decision") == "accept"
        )
        if accepted < 2 and context.get("iteration", 0) < 2:
            return True
        if not settings.OPENAI_API_KEY:
            return False
        try:
            client = LLMClient()
            memory_ctx = self.memory.get_context(job_id)
            prompt = (
                f"Query: {query}\n"
                f"Accepted results: {accepted}/{len(results)}\n"
                f"Iteration: {context.get('iteration')}\n"
                f"Should we replan? Respond with tool call."
            )
            response = await client.call_llm_with_tools(
                prompt=prompt,
                tools=AGENT_TOOLS,
                system_prompt="You are an agent orchestrator. Call replan only if results are insufficient.",
            )
            if response.raw_response and response.raw_response.get("tool_calls"):
                for tc in response.raw_response["tool_calls"]:
                    if tc.get("function", {}).get("name") == "replan":
                        return True
        except Exception as exc:
            logger.debug("Replan tool check skipped: %s", exc)
        return False

    def _extract_entity_candidates(
        self,
        query: str,
        results: Optional[List[Dict[str, Any]]],
    ) -> List[str]:
        import re
        candidates = []
        for match in re.finditer(r"\b[A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)?\b", query):
            candidates.append(match.group(0))
        if results:
            for r in results[:3]:
                title = r.get("title", "")
                for word in title.split()[:3]:
                    if word and word[0].isupper():
                        candidates.append(word)
        return list(dict.fromkeys(candidates))[:5]

    def _apply_quality_critique(
        self,
        results: List[Dict[str, Any]],
        critique_output: Optional[Dict[str, Any]],
    ) -> None:
        if not critique_output:
            return
        decision = critique_output.get("decision", critique_output)
        rejected_urls = set(decision.get("rejected", []))
        for r in results:
            url = r.get("url", "")
            if url in rejected_urls:
                r["quality_scores"]["decision"] = "reject"
                r["quality_scores"]["reason"] = "Quality critic rejected"
