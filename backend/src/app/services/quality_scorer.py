import logging
import datetime
from typing import Dict, Any
from app.services.source_registry import SourceReliabilityRegistry

logger = logging.getLogger(__name__)

class QualityScorer:
    def __init__(self):
        self.registry = SourceReliabilityRegistry()

    def calculate_relevance_score(self, query: str, title: str, snippet: str) -> float:
        """Calculate word overlap relevance score (Jaccard similarity style)."""
        if not query:
            return 0.0
            
        # Tokenize and normalize to lowercase words
        query_words = set(query.lower().split())
        content_words = set((title + " " + snippet).lower().split())
        
        if not query_words:
            return 0.0
            
        intersection = query_words.intersection(content_words)
        relevance = len(intersection) / len(query_words)
        return round(relevance, 2)

    def calculate_freshness_score(self, published_at: Any) -> float:
        """Calculate freshness score with exponential decay based on date."""
        if not published_at:
            return 0.5  # Neutral default for undated content

        try:
            if isinstance(published_at, str):
                dt = datetime.datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            elif isinstance(published_at, datetime.date) and not isinstance(published_at, datetime.datetime):
                dt = datetime.datetime.combine(published_at, datetime.time.min, tzinfo=datetime.UTC)
            elif isinstance(published_at, datetime.datetime):
                dt = published_at
            else:
                return 0.5
                
            # Ensure aware timezone
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.UTC)
                
            now = datetime.datetime.now(datetime.UTC)
            age_days = (now - dt).days
            
            if age_days < 0:
                age_days = 0
                
            # Exponential decay: freshness halves every 365 days (1 year)
            freshness = 2.0 ** (-age_days / 365.0)
            return round(max(0.1, min(1.0, freshness)), 2)
        except Exception:
            return 0.5

    def calculate_authority_score(self, url: str) -> float:
        """Determine authority based on domain extensions and depth."""
        if not url:
            return 0.4
            
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            netloc = parsed.netloc.lower()
            path = parsed.path
            
            # Simple heuristic: deeper paths on unknown domains might be slightly lower quality
            depth_penalty = min(0.2, len([p for p in path.split("/") if p]) * 0.03)
            
            # Base authority by extension
            if netloc.endswith(".gov") or netloc.endswith(".gov.uk"):
                base = 0.95
            elif netloc.endswith(".edu") or netloc.endswith(".ac.uk"):
                base = 0.95
            elif netloc.endswith(".org"):
                base = 0.80
            elif netloc.endswith(".mil"):
                base = 0.90
            else:
                base = 0.65
                
            return round(max(0.2, base - depth_penalty), 2)
        except Exception:
            return 0.5

    def score_result(self, query: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """Compute all component scores and compound final trust score."""
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        url = item.get("url", "")
        source = item.get("source", "web")
        published_at = item.get("published_at")

        relevance = self.calculate_relevance_score(query, title, snippet)
        reliability = self.registry.get_reliability_score(url, source)
        authority = self.calculate_authority_score(url)
        freshness = self.calculate_freshness_score(published_at)

        # Weighted calculation
        # relevance (35%), reliability (30%), authority (20%), freshness (15%)
        final_score = (
            0.35 * relevance +
            0.30 * reliability +
            0.20 * authority +
            0.15 * freshness
        )
        final_score = round(final_score, 2)

        # Trust Gating Decisions
        # Accept >= 0.70, Review 0.40 - 0.69, Reject < 0.40
        if final_score >= 0.70:
            decision = "accept"
            reason = "High composite trust score."
        elif final_score >= 0.40:
            decision = "review"
            reason = "Medium composite trust score. Requires validation."
        else:
            decision = "reject"
            reason = "Low composite trust score. Potential noise/spam."

        scores = {
            "relevance_score": relevance,
            "source_reliability_score": reliability,
            "freshness_score": freshness,
            "authority_score": authority,
            "entity_match_score": 0.0,
            "dedup_confidence": 0.0,
            "extraction_likelihood_score": 0.70 if decision == "accept" else 0.40,
            "risk_score": round(1.0 - reliability, 2),
            "final_trust_score": final_score,
            "decision": decision,
            "reason": reason
        }

        logger.info(
            f"QUALITY_SCORER  url='{url[:60]}'  "
            f"relevance={relevance:.2f}  "
            f"reliability={reliability:.2f}  "
            f"trust={final_score:.2f}  "
            f"decision={decision}"
        )

        return scores
