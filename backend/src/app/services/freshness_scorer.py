"""
Freshness Scorer for CredenceAI Iteration 0.3 (Sprint 53)

Determines whether a previously crawled document needs re-fetching:
- Content hash comparison (did the page change?)
- Time-decay scoring (how stale is the page?)
- Domain-specific TTL overrides
- Freshness score output (0.0 = fully stale, 1.0 = perfectly fresh)
"""

import logging
import hashlib
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Domain TTL Policy (seconds)
# ──────────────────────────────────────────────
DOMAIN_TTL_OVERRIDES: Dict[str, int] = {
    # News portals: refresh every 30 minutes
    "bbc.com": 1800,
    "reuters.com": 1800,
    "bloomberg.com": 1800,
    "techcrunch.com": 3600,
    # Reference / encyclopaedic: refresh weekly
    "en.wikipedia.org": 604800,
    "www.wikipedia.org": 604800,
    # Government / compliance: monthly
    "sec.gov": 2592000,
    "irs.gov": 2592000,
}

DEFAULT_TTL_SECONDS = 86400  # 24 hours


def _get_domain(url: str) -> str:
    """Extract the hostname from a URL string."""
    match = re.search(r"https?://([^/\?#]+)", url)
    return match.group(1).lower() if match else ""


def _get_ttl(url: str) -> int:
    """Return TTL in seconds for a URL based on domain policy."""
    domain = _get_domain(url)
    for key, ttl in DOMAIN_TTL_OVERRIDES.items():
        if domain.endswith(key):
            return ttl
    return DEFAULT_TTL_SECONDS


class FreshnessScorer:
    """
    Evaluates whether a cached document version is still fresh.

    Scoring logic:
    - If the content hash has changed → stale = True (score = 0.0)
    - If within TTL window → score decays linearly from 1.0 → 0.0
    - If beyond 2× TTL → score = 0.0 (fully stale)
    """

    def score(
        self,
        url: str,
        current_text: str,
        stored_hash: Optional[str],
        last_crawled_at: Optional[datetime],
    ) -> Dict:
        """
        Compute a freshness result dict.

        Returns:
            {
                "fresh": bool,          # True if content unchanged and within TTL
                "score": float,         # 0.0 (fully stale) → 1.0 (perfectly fresh)
                "content_changed": bool,# hash comparison result
                "staleness_seconds": int, # seconds since last crawl
                "ttl_seconds": int,     # configured TTL for this domain
                "recommend_recrawl": bool
            }
        """
        current_hash = self._hash(current_text)
        content_changed = (stored_hash is not None) and (stored_hash != current_hash)
        ttl = _get_ttl(url)

        if last_crawled_at is None:
            # Never crawled before — must fetch
            return {
                "fresh": False,
                "score": 0.0,
                "content_changed": False,
                "staleness_seconds": -1,
                "ttl_seconds": ttl,
                "current_hash": current_hash,
                "recommend_recrawl": True,
            }

        now = datetime.now(timezone.utc)
        if last_crawled_at.tzinfo is None:
            last_crawled_at = last_crawled_at.replace(tzinfo=timezone.utc)

        staleness_seconds = int((now - last_crawled_at).total_seconds())
        time_score = max(0.0, 1.0 - (staleness_seconds / ttl))

        # Content change overrides time: always stale if changed
        if content_changed:
            return {
                "fresh": False,
                "score": 0.0,
                "content_changed": True,
                "staleness_seconds": staleness_seconds,
                "ttl_seconds": ttl,
                "current_hash": current_hash,
                "recommend_recrawl": True,
            }

        fresh = staleness_seconds <= ttl
        recommend_recrawl = staleness_seconds > (ttl * 0.8)  # proactive refresh at 80%

        return {
            "fresh": fresh,
            "score": round(time_score, 4),
            "content_changed": False,
            "staleness_seconds": staleness_seconds,
            "ttl_seconds": ttl,
            "current_hash": current_hash,
            "recommend_recrawl": recommend_recrawl,
        }

    def should_recrawl(
        self,
        url: str,
        current_text: str,
        stored_hash: Optional[str],
        last_crawled_at: Optional[datetime],
    ) -> Tuple[bool, str]:
        """
        Quick decision helper: returns (should_recrawl: bool, reason: str).
        """
        result = self.score(url, current_text, stored_hash, last_crawled_at)
        if result["content_changed"]:
            return True, "content_changed"
        if not result["fresh"]:
            return True, f"stale_{result['staleness_seconds']}s"
        if result["recommend_recrawl"]:
            return True, "proactive_refresh"
        return False, "fresh"

    @staticmethod
    def _hash(text: str) -> str:
        """SHA-256 hash of normalised text content."""
        normalized = re.sub(r"\s+", " ", text).strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def hash_html(self, html: str) -> str:
        """Convenience: hash raw HTML (strips tags first)."""
        text = re.sub(r"<[^>]+>", " ", html)
        return self._hash(text)

    @staticmethod
    def get_domain_ttl(url: str) -> int:
        """Public accessor for domain TTL value."""
        return _get_ttl(url)
