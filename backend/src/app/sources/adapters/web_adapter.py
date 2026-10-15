"""
Web SourceAdapter implementation (Web Class).
Wraps SearXNG and DuckDuckGo via typed SourceAdapter protocol.
Implements FR-004, SRC-01, SRC-06, Gate G3.
"""

import time
import logging
from typing import Dict, Any, Optional
import httpx

from app.sources.protocol import (
    SourceAdapter,
    AdapterManifest,
    AdapterHit,
    AdapterResponse,
    SourceClass,
    Capability,
    CostClass,
)
from app.services.searxng_client import SearXNGClient

logger = logging.getLogger(__name__)


class WebAdapter(SourceAdapter):
    def __init__(self, searxng_client: Optional[SearXNGClient] = None):
        self._manifest = AdapterManifest(
            source_id="open_web",
            version="2.0",
            name="Open Web Search (SearXNG / DuckDuckGo)",
            source_class=SourceClass.WEB,
            enabled=True,
            executable=True,
            capabilities={Capability.METADATA},
            supported_languages=["en"],
            timeout_seconds=8.0,
            rate_limit_per_minute=60,
            cost_class=CostClass.FREE,
            legal_restrictions=["Respect robots.txt on downstream pages", "No bypass of CAPTCHA/bot challenges"],
        )
        self._client = searxng_client or SearXNGClient()

    @property
    def manifest(self) -> AdapterManifest:
        return self._manifest

    async def health_check(self) -> bool:
        return True

    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        budget: Optional[Dict[str, Any]] = None,
    ) -> AdapterResponse:
        t0 = time.perf_counter()
        limit = (budget or {}).get("max_sources", 10)

        try:
            raw_res = self._client.search(query)
            latency = (time.perf_counter() - t0) * 1000
            raw_items = raw_res.get("results", [])[:limit]

            hits = []
            for item in raw_items:
                url = item.get("url", "")
                if not url:
                    continue
                hits.append(
                    AdapterHit(
                        url=url,
                        canonical_url=item.get("canonical_url", url),
                        title=item.get("title", ""),
                        snippet=item.get("snippet") or item.get("content", ""),
                        publisher=item.get("engine") or "Web",
                        source_class=SourceClass.WEB,
                        raw_payload={"score": item.get("score"), "engine": item.get("engine")},
                    )
                )

            return AdapterResponse(
                source_id=self.manifest.source_id,
                hits=hits,
                latency_ms=latency,
                success=True,
                coverage_notes=[f"Retrieved {len(hits)} web results via {self.manifest.name}"],
            )
        except Exception as exc:
            latency = (time.perf_counter() - t0) * 1000
            logger.warning(f"WebAdapter search failed: {exc}")
            return AdapterResponse(
                source_id=self.manifest.source_id,
                hits=[],
                latency_ms=latency,
                success=False,
                error_message=str(exc),
                coverage_notes=[f"Web search unavailable: {str(exc)}"],
            )
