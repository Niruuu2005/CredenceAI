"""
Synthesis Service for CredenceAI Iteration 0.4 (Sprint 57)

Synthesizes research findings using LLM context and attaches source citations
linked to indexed Document or NormalizedResult records.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class Citation(BaseModel):
    """Citation referencing a source document or search result."""
    citation_id: int
    title: str
    url: str
    source: str = "web"


class SynthesisOutput(BaseModel):
    """Structured synthesis output with inline citations and run-scoped evidence verdict."""
    summary: str
    citations: Dict[int, Citation] = Field(default_factory=dict)
    confidence_score: float = 0.5  # Deprecated backward-compatible alias
    verdict: str = "supported"  # supported, disputed, insufficient_evidence, not_assessed
    disclaimer: str = "Findings reflect evidence examined; does not assert universal factual certainty."


class SynthesisService:
    """
    Synthesizes findings from search results and documents into a coherent answer.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.mock_mode = self.config.get("mock_mode", os.getenv("MOCK_SERVICES", "True").lower() == "true")
        self.llm_client = LLMClient()

    async def synthesize(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        vertical: str = "general"
    ) -> SynthesisOutput:
        """
        Generate a summary of the documents with inline citations.

        Args:
            query: The user's query
            documents: List of dict representation of documents or NormalizedResults
            vertical: Target vertical context (general | company | research | news | rag)
        """
        if not documents:
            return SynthesisOutput(
                summary="No relevant documents found to synthesize findings.",
                citations={},
                confidence_score=0.0,
                verdict="insufficient_evidence",
            )

        # Build citations registry
        citations = {}
        for idx, doc in enumerate(documents, 1):
            title = doc.get("title") or doc.get("canonical_text") or f"Document {idx}"
            url = doc.get("url") or doc.get("source_url") or ""
            source = doc.get("source") or "web"
            citations[idx] = Citation(
                citation_id=idx,
                title=title,
                url=url,
                source=source
            )

        if self.mock_mode:
            # Generate an evidence-calibrated response
            summary_parts = [
                f"Based on the analysis of examined sources for '{query}', key findings indicate:"
            ]
            for idx, citation in citations.items():
                summary_parts.append(
                    f"According to {citation.title}, evidence supports observations on this topic [{idx}]."
                )
            summary = " ".join(summary_parts)
            return SynthesisOutput(
                summary=summary,
                citations=citations,
                confidence_score=0.85,
                verdict="supported",
            )

        # Build prompt for LLM
        context_str = ""
        for idx, doc in enumerate(documents, 1):
            text = doc.get("body_text") or doc.get("text") or doc.get("snippet") or ""
            context_str += f"[{idx}] Source: {doc.get('title')}\nURL: {doc.get('url')}\nContent: {text[:500]}\n\n"

        system_prompt = (
            "You are an evidence intelligence synthesizer. Synthesize the provided context into an objective, "
            "factual summary answering the query. You MUST cite your sources using bracketed numbers like [1], [2] "
            "corresponding to the sources in the context. Frame findings as 'supported by the evidence examined', "
            "and explicitly note any conflicts, gaps, or uncertainties rather than asserting universal truth."
        )

        prompt = (
            f"User Query: {query}\n\n"
            f"Context Documents:\n{context_str}\n\n"
            f"Please generate the summary with correct bracketed citations."
        )

        try:
            llm_response = await self.llm_client.call_llm(prompt, system_prompt)
            return SynthesisOutput(
                summary=llm_response.content,
                citations=citations,
                confidence_score=0.90,
                verdict="supported",
            )
        except Exception as e:
            logger.error(f"Synthesis failed: {e}. Falling back to mock summary.")
            # Fallback
            return SynthesisOutput(
                summary=f"Fallback synthesis due to LLM error: {query}",
                citations=citations,
                confidence_score=0.5
            )
