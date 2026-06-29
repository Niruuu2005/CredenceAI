"""
Vertical Packs for CredenceAI Iteration 0.4 (Sprint 57)

Specialized logic for:
- Company Pack: extracts competitors, founders, funding events.
- RAG Pack: exports clean JSON/CSV datasets ready to train/fine-tune LLM models or feed RAG pipelines.
"""

import json
import csv
import io
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CompanyProfile(BaseModel):
    """Structured company intelligence profile."""
    company_name: str
    description: str = ""
    founders: List[str] = Field(default_factory=list)
    competitors: List[str] = Field(default_factory=list)
    funding_events: List[Dict[str, Any]] = Field(default_factory=list)
    key_metrics: Dict[str, Any] = Field(default_factory=dict)


class CompanyPack:
    """Specialized service for company intelligence and competitor set extraction."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def extract_profile(
        self,
        company_name: str,
        facts: List[Dict[str, Any]],
        related_entities: List[str] = None
    ) -> CompanyProfile:
        """
        Analyze facts from the evidence graph to build a structured CompanyProfile.
        """
        founders = []
        competitors = []
        funding_events = []
        key_metrics = {}

        # Heuristic extraction from factual text
        for fact in facts:
            text = fact.get("claim") or fact.get("canonical_text") or ""
            text_lower = text.lower()

            # Founder extraction heuristic
            if "founded by" in text_lower or "founder" in text_lower:
                # E.g., "Founded by John Doe and Jane Smith"
                import re
                names = re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b", text)
                for name in names:
                    if name.lower() != company_name.lower() and name not in founders:
                        founders.append(name)

            # Competitor extraction heuristic
            if "competitor" in text_lower or "competes with" in text_lower or "rival" in text_lower:
                import re
                names = re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b", text)

                for name in names:
                    if name.lower() != company_name.lower() and name not in competitors:
                        competitors.append(name)

            # Funding event heuristic
            if "raised" in text_lower or "funding" in text_lower or "series" in text_lower:
                import re
                amount_match = re.search(r"\$\d+(?:\.\d+)?\s*(?:million|billion|M|B)?", text)
                round_match = re.search(r"\b(?:Series [A-Z]|Seed|Pre-seed|IPO)\b", text, re.IGNORECASE)
                if amount_match or round_match:
                    funding_events.append({
                        "round": round_match.group(0) if round_match else "Unknown",
                        "amount": amount_match.group(0) if amount_match else "Unknown",
                        "description": text
                    })

        # Augment competitors with related entities if empty
        if not competitors and related_entities:
            competitors = [entity for entity in related_entities if entity.lower() != company_name.lower()][:5]

        # Clean duplicates
        founders = list(dict.fromkeys(founders))
        competitors = list(dict.fromkeys(competitors))

        return CompanyProfile(
            company_name=company_name,
            description=f"Generated profile for {company_name}",
            founders=founders,
            competitors=competitors,
            funding_events=funding_events,
            key_metrics=key_metrics
        )


class RAGPack:
    """Specialized service to format/export dataset packs for training/indexing RAG systems."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def export_json(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        synthesis: str
    ) -> str:
        """Export RAG context-answer pair in JSON format."""
        data = {
            "instruction": query,
            "context": [
                {
                    "title": doc.get("title") or "",
                    "url": doc.get("url") or "",
                    "text": doc.get("body_text") or doc.get("text") or doc.get("snippet") or ""
                }
                for doc in documents
            ],
            "response": synthesis
        }
        return json.dumps(data, indent=2)

    def export_csv(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        synthesis: str
    ) -> str:
        """Export RAG training/validation pair in CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["instruction", "context", "response"])
        
        # Flattened context
        context_str = "\n---\n".join([
            f"Source: {doc.get('title')}\nContent: {doc.get('body_text') or doc.get('text') or doc.get('snippet') or ''}"
            for doc in documents
        ])
        writer.writerow([query, context_str, synthesis])
        return output.getvalue()
