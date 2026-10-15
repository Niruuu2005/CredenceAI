"""
Unit and integration tests for source adapters, registry, and router.
Verifies FR-004, FR-005, SRC-01 to SRC-14, Release Gate G3, Acceptance Scenario AT-03.
"""

import pytest
import asyncio
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
from app.sources.registry import SourceRegistry
from app.sources.router import SourceRouter, CoverageReport
from app.sources.adapters.wikipedia_adapter import WikipediaAdapter
from app.sources.adapters.scholarly_adapter import OpenAlexScholarlyAdapter, reconstruct_abstract


class MockTimedOutAdapter(SourceAdapter):
    """Mock adapter that simulates an upstream network timeout."""
    def __init__(self):
        self._manifest = AdapterManifest(
            source_id="slow_provider",
            version="1.0",
            name="Slow Mock Provider",
            source_class=SourceClass.NEWS,
            timeout_seconds=0.05,
        )

    @property
    def manifest(self) -> AdapterManifest:
        return self._manifest

    async def health_check(self) -> bool:
        return True

    async def search(self, query: str, filters=None, budget=None) -> AdapterResponse:
        await asyncio.sleep(0.5)  # Intentionally exceeds timeout
        return AdapterResponse(source_id="slow_provider", hits=[], latency_ms=500, success=True)


class MockHealthyAdapter(SourceAdapter):
    """Mock adapter that returns clean simulated hits."""
    def __init__(self, source_id: str, source_class: SourceClass):
        self._manifest = AdapterManifest(
            source_id=source_id,
            version="1.0",
            name=f"Mock {source_id.title()}",
            source_class=source_class,
        )

    @property
    def manifest(self) -> AdapterManifest:
        return self._manifest

    async def health_check(self) -> bool:
        return True

    async def search(self, query: str, filters=None, budget=None) -> AdapterResponse:
        hits = [
            AdapterHit(
                url=f"https://{self._manifest.source_id}.org/item1",
                canonical_url=f"https://{self._manifest.source_id}.org/item1",
                title=f"Finding from {self._manifest.name}",
                snippet=f"Detailed passage content regarding {query}",
                publisher=self._manifest.name,
                source_class=self._manifest.source_class,
            )
        ]
        return AdapterResponse(
            source_id=self._manifest.source_id,
            hits=hits,
            latency_ms=12.5,
            success=True,
            coverage_notes=[f"Successfully retrieved 1 hit from {self._manifest.source_id}"],
        )


@pytest.mark.asyncio
async def test_three_executable_source_classes_registered():
    """
    RELEASE GATE G3 & SRC-06:
    Verify presence of at least three distinct executable source classes:
    REFERENCE, WEB, and SCHOLARLY.
    """
    registry = SourceRegistry()
    ref_adapter = MockHealthyAdapter("wikipedia_ref", SourceClass.REFERENCE)
    web_adapter = MockHealthyAdapter("duckduckgo_web", SourceClass.WEB)
    scholarly_adapter = MockHealthyAdapter("openalex_scholarly", SourceClass.SCHOLARLY)

    registry.register(ref_adapter)
    registry.register(web_adapter)
    registry.register(scholarly_adapter)

    classes_present = {a.manifest.source_class for a in registry.list_executable()}
    assert SourceClass.REFERENCE in classes_present
    assert SourceClass.WEB in classes_present
    assert SourceClass.SCHOLARLY in classes_present
    assert len(classes_present) >= 3


@pytest.mark.asyncio
async def test_source_router_at_03_provider_timeout_preserves_partial_coverage():
    """
    ACCEPTANCE SCENARIO AT-03:
    One of three adapters times out -> run shows partial coverage, notes the failure,
    and returns hits from the other healthy providers without crashing.
    """
    registry = SourceRegistry()
    ref_adapter = MockHealthyAdapter("wikipedia_ref", SourceClass.REFERENCE)
    scholarly_adapter = MockHealthyAdapter("openalex_scholarly", SourceClass.SCHOLARLY)
    failing_adapter = MockTimedOutAdapter()

    registry.register(ref_adapter)
    registry.register(scholarly_adapter)
    registry.register(failing_adapter)

    router = SourceRouter(registry)

    # Search with bounded timeout
    res = await router.route_and_search(query="climate impact", budget={"timeout_seconds": 0.1})

    # Coverage report must explicitly reflect reality
    assert "wikipedia_ref" in res.coverage.successful_sources
    assert "openalex_scholarly" in res.coverage.successful_sources
    assert "slow_provider" in res.coverage.queried_sources
    # Slow provider must be in failed sources
    assert "slow_provider" in res.coverage.failed_sources
    # Total hits must include results from successful providers
    assert res.coverage.total_hits == 2
    assert len(res.hits) == 2


@pytest.mark.asyncio
async def test_source_router_skips_unhealthy_or_disabled_adapters():
    """
    SRC-03 / SRC-12:
    Disabled or unhealthy adapters must be skipped with explicit diagnostics recorded.
    """
    registry = SourceRegistry()
    active = MockHealthyAdapter("active_provider", SourceClass.WEB)
    disabled_manifest = AdapterManifest(
        source_id="disabled_provider",
        version="1.0",
        name="Disabled Provider",
        source_class=SourceClass.WEB,
        enabled=False,
    )

    class DisabledAdapter(SourceAdapter):
        @property
        def manifest(self):
            return disabled_manifest
        async def health_check(self):
            return False
        async def search(self, query, filters=None, budget=None):
            return AdapterResponse(source_id="disabled_provider", hits=[], latency_ms=0, success=False)

    registry.register(active)
    registry.register(DisabledAdapter())

    router = SourceRouter(registry)
    res = await router.route_and_search(query="local tax policy")

    assert "active_provider" in res.coverage.successful_sources
    assert "disabled_provider" in res.coverage.skipped_sources
    assert "disabled" in res.coverage.skipped_sources["disabled_provider"].lower()


@pytest.mark.asyncio
async def test_wikipedia_adapter_mocked_http():
    """Verify WikipediaAdapter parses Wikipedia API search results correctly."""
    mock_payload = {
        "query": {
            "search": [
                {
                    "title": "Renewable energy",
                    "pageid": 12345,
                    "snippet": "Renewable energy is <span class=\"searchmatch\">energy</span> collected from resources...",
                    "timestamp": "2026-08-01T12:00:00Z",
                    "wordcount": 4500,
                }
            ]
        }
    }

    class MockTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            return httpx.Response(200, json=mock_payload)

    client = httpx.AsyncClient(transport=MockTransport())
    adapter = WikipediaAdapter(client=client)

    response = await adapter.search("renewable energy")
    assert response.success is True
    assert len(response.hits) == 1
    hit = response.hits[0]
    assert hit.title == "Renewable energy"
    assert "https://en.wikipedia.org/wiki/Renewable_energy" in hit.url
    assert "<span" not in hit.snippet  # HTML searchmatch tag stripped
    assert hit.source_class == SourceClass.REFERENCE


@pytest.mark.asyncio
async def test_openalex_scholarly_adapter_mocked_http():
    """Verify OpenAlexScholarlyAdapter parses academic paper metadata and reconstructs abstract."""
    mock_payload = {
        "results": [
            {
                "id": "https://openalex.org/W123456",
                "doi": "https://doi.org/10.1000/182",
                "title": "Quantum Error Correction Protocols",
                "publication_date": "2026-01-15",
                "cited_by_count": 42,
                "primary_location": {
                    "source": {"display_name": "Physical Review Letters"},
                    "landing_page_url": "https://doi.org/10.1000/182",
                },
                "authorships": [
                    {"author": {"display_name": "Dr. Shannon"}},
                    {"author": {"display_name": "Dr. Turing"}},
                ],
                "abstract_inverted_index": {
                    "Quantum": [0],
                    "computing": [1],
                    "requires": [2],
                    "fault-tolerant": [3],
                    "thresholds.": [4],
                },
            }
        ]
    }

    class MockTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            return httpx.Response(200, json=mock_payload)

    client = httpx.AsyncClient(transport=MockTransport())
    adapter = OpenAlexScholarlyAdapter(client=client)

    response = await adapter.search("quantum error correction")
    assert response.success is True
    assert len(response.hits) == 1
    hit = response.hits[0]
    assert hit.title == "Quantum Error Correction Protocols"
    assert hit.author == "Dr. Shannon, Dr. Turing"
    assert hit.publisher == "Physical Review Letters"
    assert hit.published_at == "2026-01-15"
    assert hit.snippet == "Quantum computing requires fault-tolerant thresholds."
    assert hit.source_class == SourceClass.SCHOLARLY
