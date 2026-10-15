"""
Source intelligence module for CredenceAI 2.0.
Provides typed source adapters, manifests, registry, and health-aware routing.
"""

from app.sources.protocol import (
    SourceAdapter,
    AdapterManifest,
    AdapterHit,
    AdapterResponse,
    SourceClass,
    Capability,
    CostClass,
)
from app.sources.registry import SourceRegistry, source_registry
from app.sources.router import SourceRouter, CoverageReport, MultiSourceSearchResult
from app.sources.adapters.wikipedia_adapter import WikipediaAdapter
from app.sources.adapters.web_adapter import WebAdapter
from app.sources.adapters.scholarly_adapter import OpenAlexScholarlyAdapter

__all__ = [
    "SourceAdapter",
    "AdapterManifest",
    "AdapterHit",
    "AdapterResponse",
    "SourceClass",
    "Capability",
    "CostClass",
    "SourceRegistry",
    "source_registry",
    "SourceRouter",
    "CoverageReport",
    "MultiSourceSearchResult",
    "WikipediaAdapter",
    "WebAdapter",
    "OpenAlexScholarlyAdapter",
]
