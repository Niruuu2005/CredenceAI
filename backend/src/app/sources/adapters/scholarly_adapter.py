"""
Scholarly SourceAdapter implementation (Scholarly Class via OpenAlex).
Implements FR-004, SRC-01, SRC-06, Gate G3.
"""

import time
import logging
from typing import Dict, Any, Optional, List
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

logger = logging.getLogger(__name__)


def reconstruct_abstract(abstract_inverted_index: Optional[Dict[str, List[int]]]) -> str:
    """Reconstruct plain text from OpenAlex inverted abstract index."""
    if not abstract_inverted_index:
        return ""
    word_positions = []
    for word, positions in abstract_inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort(key=lambda x: x[0])
    return " ".join([word for _, word in word_positions])


class OpenAlexScholarlyAdapter(SourceAdapter):
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._manifest = AdapterManifest(
            source_id="openalex_scholarly",
            version="2.0",
            name="OpenAlex Scholarly Literature",
            source_class=SourceClass.SCHOLARLY,
            enabled=True,
            executable=True,
            capabilities={Capability.METADATA, Capability.HISTORICAL},
            supported_languages=["en"],
            timeout_seconds=8.0,
            rate_limit_per_minute=100,
            cost_class=CostClass.FREE,
            legal_restrictions=["CC0 public domain dedication for OpenAlex metadata"],
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

        url = "https://api.openalex.org/works"
        params = {
            "search": query,
            "per-page": min(limit, 10),
        }
        headers = {
            "User-Agent": "CredenceAI/2.0 (mailto:research@credenceai.org)",
        }

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
                    error_message=f"OpenAlex returned HTTP {response.status_code}",
                    coverage_notes=[f"OpenAlex returned HTTP {response.status_code}"],
                )

            data = response.json()
            works = data.get("results", [])
            hits = []

            for work in works:
                title = work.get("title") or "Untitled Academic Work"
                doi = work.get("doi")
                landing_page = work.get("primary_location", {}).get("landing_page_url") or doi or work.get("id")
                
                # Authors
                authorships = work.get("authorships", [])
                author_names = [a.get("author", {}).get("display_name") for a in authorships if a.get("author")]
                author_str = ", ".join(author_names[:3])
                if len(author_names) > 3:
                    author_str += " et al."

                # Venue / Publisher
                venue = work.get("primary_location", {}).get("source", {}) or {}
                publisher = venue.get("display_name") or "Scholarly Publication"

                abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
                snippet = abstract[:400] if abstract else f"Published in {publisher}. Cited by {work.get('cited_by_count', 0)} papers."

                hits.append(
                    AdapterHit(
                        url=landing_page,
                        canonical_url=doi or landing_page,
                        title=title,
                        snippet=snippet,
                        publisher=publisher,
                        author=author_str,
                        published_at=work.get("publication_date"),
                        source_class=SourceClass.SCHOLARLY,
                        raw_payload={
                            "openalex_id": work.get("id"),
                            "doi": doi,
                            "cited_by_count": work.get("cited_by_count"),
                            "is_oa": work.get("open_access", {}).get("is_oa", False),
                        },
                    )
                )

            return AdapterResponse(
                source_id=self.manifest.source_id,
                hits=hits,
                latency_ms=latency,
                success=True,
                coverage_notes=[f"Retrieved {len(hits)} scholarly papers from OpenAlex"],
            )

        except Exception as exc:
            latency = (time.perf_counter() - t0) * 1000
            logger.warning(f"OpenAlex query failed: {exc}")
            return AdapterResponse(
                source_id=self.manifest.source_id,
                hits=[],
                latency_ms=latency,
                success=False,
                error_message=str(exc),
                coverage_notes=[f"Scholarly discovery error: {str(exc)}"],
            )
