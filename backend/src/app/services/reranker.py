"""
Reranker Service for CredenceAI Iteration 0.5 (Sprint 59)

Applies a Cross-Encoder model (or lightweight semantic overlap scoring fallback)
to rerank candidate search results for optimal retrieval precision.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class Reranker:
    """
    Reranks search results based on semantic query-document similarity.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        # In production, this can initialize a Hugging Face CrossEncoder
        # E.g., CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        self.model = None

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Rerank a list of candidates using semantic similarity.

        Args:
            query: User search query
            candidates: List of normalized result dictionaries
            top_n: Number of results to return
        """
        if not candidates:
            return []

        logger.info(f"RERANKER  candidates={len(candidates)}  query='{query[:40]}'")

        scored_candidates = []
        for cand in candidates:
            score = self._compute_similarity_score(query, cand)
            # Combine or overwrite with the new rerank score
            cand_copy = dict(cand)
            cand_copy["rerank_score"] = round(score, 4)
            # Adjust final trust score/quality score if available
            if "quality_score" in cand_copy:
                cand_copy["quality_score"] = round(0.4 * cand_copy["quality_score"] + 0.6 * score, 4)
            scored_candidates.append(cand_copy)

        # Sort by rerank score descending
        scored_candidates.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        return scored_candidates[:top_n]

    def _compute_similarity_score(self, query: str, candidate: Dict[str, Any]) -> float:
        """
        Compute similarity score between query and candidate.
        Uses character n-gram / Jaccard similarity fallback.
        """
        query_words = set(query.lower().split())
        title = (candidate.get("title") or "").lower()
        snippet = (candidate.get("snippet") or "").lower()
        
        doc_words = set(title.split() + snippet.split())
        
        if not query_words or not doc_words:
            return 0.1
            
        intersection = query_words.intersection(doc_words)
        union = query_words.union(doc_words)
        
        # Jaccard index
        jaccard = len(intersection) / len(union)
        
        # Phrase match boost
        phrase_boost = 0.0
        if query.lower() in title or query.lower() in snippet:
            phrase_boost = 0.3
            
        return min(1.0, 0.2 + 0.5 * jaccard + phrase_boost)
