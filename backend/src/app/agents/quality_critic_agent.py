"""
Quality Critic Agent for CredenceAI Iteration 0.4 (Sprint 54)

Evaluates the quality of collected source documents and provides a
structured critique including:
- Relevance to query
- Source credibility score
- Freshness score
- Content density score
- Overall quality verdict (accept / review / reject)
"""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class DocumentQualityInput(BaseModel):
    """Input for a single document quality check."""
    url: str
    title: str = ""
    text: str
    source_name: str = "unknown"
    word_count: int = 0
    token_count: int = 0
    published_date: Optional[str] = None
    content_hash: Optional[str] = None


class QualityCritiqueOutput(BaseModel):
    """Quality critique for a set of documents."""
    accepted: List[str]      # URLs of accepted documents
    review: List[str]         # URLs needing manual review
    rejected: List[str]       # URLs of rejected documents
    scores: Dict[str, float]  # URL -> quality score
    reasoning: str
    confidence_score: float = Field(ge=0.0, le=1.0)


# Domain-level credibility overrides
CREDIBLE_DOMAINS = {
    "arxiv.org": 0.90,
    "pubmed.ncbi.nlm.nih.gov": 0.95,
    "nature.com": 0.95,
    "scholar.google.com": 0.85,
    "wikipedia.org": 0.80,
    "reuters.com": 0.88,
    "bbc.com": 0.85,
    "wikidata.org": 0.90,
    "sec.gov": 0.92,
}

BLOCKED_DOMAINS = {
    "spam-news.com",
    "fake-research.net",
    "clickbait.co",
}


class QualityCriticAgent(BaseAgent):
    """
    Agent that critiques and filters collected source documents.

    Scoring dimensions:
    1. Relevance (keyword overlap with query)
    2. Credibility (domain reputation)
    3. Freshness (publication date decay)
    4. Density (word/token ratio suggesting quality content)

    Verdicts:
    - accept: score >= 0.70
    - review: 0.40 <= score < 0.70
    - reject: score < 0.40 or blocked domain
    """

    agent_name = "quality_critic_agent"
    agent_description = "Evaluates and filters source documents by quality, credibility and relevance"

    ACCEPT_THRESHOLD = 0.70
    REVIEW_THRESHOLD = 0.40
    MIN_WORD_COUNT = 50

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config=config or {})

    def validate_input(self, agent_input: AgentInput) -> bool:
        if "query" not in agent_input.context:
            raise ValueError("Missing required field: query")
        if "documents" not in agent_input.context:
            raise ValueError("Missing required field: documents (list of document dicts)")
        return True

    async def invoke(self, agent_input: AgentInput) -> AgentOutput:
        query = agent_input.context["query"]
        documents: List[Dict] = agent_input.context["documents"]

        accepted, review, rejected, scores = [], [], [], {}
        doc_summaries = []

        for doc in documents:
            url = doc.get("url", "")
            score = self._score_document(query, doc)
            scores[url] = round(score, 4)

            domain = self._extract_domain(url)
            if domain in BLOCKED_DOMAINS:
                rejected.append(url)
                doc_summaries.append(f"REJECTED({url[:40]}): blocked domain")
            elif score >= self.ACCEPT_THRESHOLD:
                accepted.append(url)
                doc_summaries.append(f"ACCEPT({url[:40]}): score={score:.2f}")
            elif score >= self.REVIEW_THRESHOLD:
                review.append(url)
                doc_summaries.append(f"REVIEW({url[:40]}): score={score:.2f}")
            else:
                rejected.append(url)
                doc_summaries.append(f"REJECT({url[:40]}): score={score:.2f}")

        avg_score = sum(scores.values()) / len(scores) if scores else 0.0
        reasoning = (
            f"Evaluated {len(documents)} documents for query '{query[:80]}'. "
            f"Accepted: {len(accepted)}, Review: {len(review)}, Rejected: {len(rejected)}. "
            f"Avg score: {avg_score:.2f}. Details: {'; '.join(doc_summaries[:5])}"
        )

        output = QualityCritiqueOutput(
            accepted=accepted,
            review=review,
            rejected=rejected,
            scores=scores,
            reasoning=reasoning,
            confidence_score=round(min(avg_score + 0.1, 1.0), 4),
        )

        return AgentOutput(
            decision=output.model_dump(),
            reasoning=reasoning,
            confidence_score=output.confidence_score,
            metadata={
                "total": len(documents),
                "accepted": len(accepted),
                "review": len(review),
                "rejected": len(rejected),
            },
        )

    def parse_output(self, raw_output: Any) -> AgentOutput:
        if isinstance(raw_output, AgentOutput):
            return raw_output
        return AgentOutput(
            decision=str(raw_output),
            reasoning="Parsed from raw output",
            confidence_score=0.5,
        )

    # ──────────────────────────────────────────────
    # Scoring helpers
    # ──────────────────────────────────────────────

    def _score_document(self, query: str, doc: Dict) -> float:
        """Compute overall quality score [0.0, 1.0] for a document."""
        relevance = self._score_relevance(query, doc.get("text", ""), doc.get("title", ""))
        credibility = self._score_credibility(doc.get("url", ""))
        freshness = self._score_freshness(doc.get("published_date"))
        density = self._score_density(doc.get("word_count", 0), doc.get("token_count", 0), doc.get("text", ""))

        # Weighted average
        score = (
            relevance * 0.35
            + credibility * 0.30
            + freshness * 0.20
            + density * 0.15
        )
        return max(0.0, min(1.0, score))

    def _score_relevance(self, query: str, text: str, title: str) -> float:
        """Keyword overlap between query and document text+title."""
        query_terms = set(re.findall(r"\w+", query.lower()))
        doc_terms = set(re.findall(r"\w+", (text + " " + title).lower()))
        if not query_terms:
            return 0.5
        overlap = len(query_terms & doc_terms) / len(query_terms)
        return min(1.0, overlap * 1.5)  # boost since documents are longer

    def _score_credibility(self, url: str) -> float:
        """Return credibility score based on domain reputation."""
        domain = self._extract_domain(url)
        for known_domain, score in CREDIBLE_DOMAINS.items():
            if domain.endswith(known_domain):
                return score
        # Unknown domain: neutral credibility
        return 0.60

    def _score_freshness(self, published_date: Optional[str]) -> float:
        """Time-decay freshness score (1.0 = very recent, 0.0 = very old)."""
        if not published_date:
            return 0.5  # unknown — neutral

        try:
            # Try ISO format with various suffixes
            clean_date = published_date[:10]  # YYYY-MM-DD
            pub_dt = datetime.strptime(clean_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            age_days = (now - pub_dt).days
            # Linear decay: 100% fresh at 0 days, 0% at 2 years (730 days)
            return max(0.0, 1.0 - (age_days / 730))
        except Exception:
            return 0.5

    def _score_density(self, word_count: int, token_count: int, text: str) -> float:
        """Content density: penalise very short or very sparse documents."""
        wc = word_count or len(text.split())
        if wc < self.MIN_WORD_COUNT:
            return 0.2
        if wc < 200:
            return 0.5
        if wc < 500:
            return 0.75
        return 1.0

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract the hostname from a URL."""
        match = re.search(r"https?://([^/\?#]+)", url)
        return match.group(1).lower() if match else ""
