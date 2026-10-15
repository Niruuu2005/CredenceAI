"""
Wikipedia SourceAdapter implementation (Reference Class).
Implements FR-004, SRC-01, SRC-06, Gate G3.
"""

import time
import urllib.parse
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


class WikipediaAdapter(SourceAdapter):
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._manifest = AdapterManifest(
            source_id="wikipedia",
            version="2.0",
            name="Wikipedia Reference Knowledge",
            source_class=SourceClass.REFERENCE,
            enabled=True,
            executable=True,
            capabilities={Capability.METADATA, Capability.FULL_TEXT},
            supported_languages=["en"],
            timeout_seconds=5.0,
            rate_limit_per_minute=120,
            cost_class=CostClass.FREE,
            legal_restrictions=["CC BY-SA 4.0 license", "No commercial redistribution restrictions"],
        )
        self._client = client

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
        timeout = (budget or {}).get("timeout_seconds", self.manifest.timeout_seconds)
        limit = (budget or {}).get("max_sources", 5)

        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": min(limit, 10),
            "format": "json",
        }
        url = "https://en.wikipedia.org/w/api.php"
        headers = {"User-Agent": "CredenceAI/2.0 (research-platform@credenceai.org)"}

        try:
            if self._client:
                response = await self._client.get(url, params=params, headers=headers, timeout=timeout)
            else:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(url, params=params, headers=headers)

            latency = (time.perf_counter() - t0) * 1000
            if response.status_code != 200:
                return AdapterResponse(
                    source_id=self.manifest.source_id,
                    hits=[],
                    latency_ms=latency,
                    success=False,
                    status_code=response.status_code,
                    error_message=f"Upstream returned HTTP {response.status_code}",
                    coverage_notes=[f"Wikipedia returned HTTP {response.status_code}"],
                )

            data = response.json()
            raw_hits = data.get("query", {}).get("search", [])
            hits = []

            for item in raw_hits:
                title = item.get("title", "")
                page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                # Clean HTML tags like <span class="searchmatch">
                raw_snippet = item.get("snippet", "")
                clean_snippet = raw_snippet.replace('<span class="searchmatch">', "").replace("</span>", "")

                hits.append(
                    AdapterHit(
                        url=page_url,
                        canonical_url=page_url,
                        title=title,
                        snippet=clean_snippet,
                        publisher="Wikipedia",
                        published_at=item.get("timestamp"),
                        source_class=SourceClass.REFERENCE,
                        raw_payload={"pageid": item.get("pageid"), "wordcount": item.get("wordcount")},
                    )
                )

            return AdapterResponse(
                source_id=self.manifest.source_id,
                hits=hits,
                latency_ms=latency,
                success=True,
                coverage_notes=[f"Retrieved {len(hits)} reference articles from Wikipedia"],
            )

        except Exception as exc:
            latency = (time.perf_counter() - t0) * 1000
            return AdapterResponse(
                source_id=self.manifest.source_id,
                hits=[],
                latency_ms=latency,
                success=False,
                error_message=str(exc),
                coverage_notes=[f"Wikipedia query error: {str(exc)}"],
            )
