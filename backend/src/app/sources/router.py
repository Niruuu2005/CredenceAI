"""
Health-aware multi-source router with transparent coverage diagnostics.
Implements FR-004, FR-005, SRC-03, SRC-04, SRC-05, SRC-12, SRC-13, AT-03.
"""

import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from app.sources.protocol import SourceAdapter, SourceClass, AdapterHit
from app.sources.registry import SourceRegistry, source_registry

logger = logging.getLogger(__name__)


@dataclass
class CoverageReport:
    """
    Transparent record of provider execution, skips, and failures.
    Ensures zero silent failures and honest coverage reporting.
    """
    queried_sources: List[str] = field(default_factory=list)
    successful_sources: List[str] = field(default_factory=list)
    skipped_sources: Dict[str, str] = field(default_factory=dict)
    failed_sources: Dict[str, str] = field(default_factory=dict)
    total_hits: int = 0
    stage_duration_ms: float = 0.0
    notes: List[str] = field(default_factory=list)


@dataclass
class MultiSourceSearchResult:
    """Consolidated multi-source search results and coverage report."""
    hits: List[AdapterHit]
    coverage: CoverageReport


class SourceRouter:
    def __init__(self, registry: Optional[SourceRegistry] = None):
        self.registry = registry or source_registry

    def select_adapters(
        self,
        mode: str = "investigate",
        requested_classes: Optional[List[SourceClass]] = None,
        language: str = "en",
    ) -> tuple[List[SourceAdapter], Dict[str, str]]:
        """
        Determine eligible adapters and explain why non-eligible ones are skipped.
        """
        eligible: List[SourceAdapter] = []
        skipped: Dict[str, str] = {}

        all_adapters = self.registry.list_all()

        for adapter in all_adapters:
            manifest = adapter.manifest
            source_id = manifest.source_id

            if not manifest.enabled:
                skipped[source_id] = "Adapter is disabled in configuration."
                continue

            if not manifest.executable:
                skipped[source_id] = "Adapter is marked non-executable (missing upstream credentials/endpoint)."
                continue

            if not self.registry._health_status.get(source_id, True):
                skipped[source_id] = "Upstream provider is currently marked unhealthy."
                continue

            if language not in manifest.supported_languages:
                skipped[source_id] = f"Language '{language}' not supported by adapter."
                continue

            if requested_classes and manifest.source_class not in requested_classes:
                skipped[source_id] = f"Source class '{manifest.source_class.value}' not requested for this run."
                continue

            eligible.append(adapter)

        return eligible, skipped

    async def route_and_search(
        self,
        query: str,
        mode: str = "investigate",
        requested_classes: Optional[List[SourceClass]] = None,
        language: str = "en",
        budget: Optional[Dict[str, Any]] = None,
    ) -> MultiSourceSearchResult:
        t0 = time.perf_counter()
        coverage = CoverageReport()

        eligible, skipped = self.select_adapters(
            mode=mode,
            requested_classes=requested_classes,
            language=language,
        )
        coverage.skipped_sources = skipped

        if not eligible:
            coverage.notes.append("No eligible source adapters available for this query and mode.")
            coverage.stage_duration_ms = (time.perf_counter() - t0) * 1000
            return MultiSourceSearchResult(hits=[], coverage=coverage)

        coverage.queried_sources = [a.manifest.source_id for a in eligible]

        # Execute all eligible adapters concurrently under bounded deadlines
        async def _run_adapter(adapter: SourceAdapter):
            manifest = adapter.manifest
            adapter_timeout = min(
                (budget or {}).get("timeout_seconds", manifest.timeout_seconds),
                manifest.timeout_seconds,
            )
            try:
                resp = await asyncio.wait_for(
                    adapter.search(query=query, budget=budget),
                    timeout=adapter_timeout,
                )
                return manifest.source_id, resp, None
            except (asyncio.TimeoutError, TimeoutError):
                return manifest.source_id, None, f"Timeout exceeded ({adapter_timeout:.2f}s) waiting for provider response."
            except Exception as e:
                return manifest.source_id, None, str(e)

        tasks = [_run_adapter(a) for a in eligible]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_hits: List[AdapterHit] = []

        for res in results:
            if isinstance(res, Exception):
                logger.error(f"Unexpected adapter execution exception: {res}")
                coverage.notes.append(f"Unexpected runner exception: {res}")
                continue

            source_id, resp, err = res

            if err:
                coverage.failed_sources[source_id] = err
                coverage.notes.append(f"Adapter '{source_id}' failed: {err}")
            elif resp and not resp.success:
                coverage.failed_sources[source_id] = resp.error_message or "Unknown failure"
                coverage.notes.extend(resp.coverage_notes)
            elif resp and resp.success:
                coverage.successful_sources.append(source_id)
                coverage.notes.extend(resp.coverage_notes)
                all_hits.extend(resp.hits)

        coverage.total_hits = len(all_hits)
        coverage.stage_duration_ms = (time.perf_counter() - t0) * 1000

        logger.info(
            f"SOURCE_ROUTER  query='{query[:50]}'  "
            f"queried={len(coverage.queried_sources)}  "
            f"success={len(coverage.successful_sources)}  "
            f"failed={len(coverage.failed_sources)}  "
            f"total_hits={coverage.total_hits}  "
            f"elapsed={coverage.stage_duration_ms:.2f}ms"
        )

        return MultiSourceSearchResult(hits=all_hits, coverage=coverage)
