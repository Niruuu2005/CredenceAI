"""
Typed SourceAdapter protocol and versioned manifest schema.
Implements FR-004, SRC-01, SRC-02, SRC-07.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set, Dict, Any


class SourceClass(str, Enum):
    WEB = "web"
    REFERENCE = "reference"
    SCHOLARLY = "scholarly"
    NEWS = "news"
    ARCHIVE = "archive"


class Capability(str, Enum):
    METADATA = "metadata"
    FULL_TEXT = "full_text"
    HISTORICAL = "historical"


class CostClass(str, Enum):
    FREE = "free"
    FREEMIUM = "freemium"
    PAID = "paid"


@dataclass(frozen=True)
class AdapterManifest:
    """
    Metadata describing an adapter's operational capabilities, limits, and legal constraints.
    """
    source_id: str
    version: str
    name: str
    source_class: SourceClass
    enabled: bool = True
    executable: bool = True
    capabilities: Set[Capability] = field(default_factory=lambda: {Capability.METADATA})
    supported_languages: List[str] = field(default_factory=lambda: ["en"])
    timeout_seconds: float = 10.0
    rate_limit_per_minute: int = 60
    cost_class: CostClass = CostClass.FREE
    legal_restrictions: List[str] = field(default_factory=list)


@dataclass
class AdapterHit:
    """
    Normalized result hit returned by an adapter.
    Preserves provenance details without collapsing independent corroboration.
    """
    url: str
    title: str
    snippet: str
    canonical_url: Optional[str] = None
    publisher: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[str] = None  # ISO format string or None
    source_class: SourceClass = SourceClass.WEB
    raw_payload: Optional[Dict[str, Any]] = None


@dataclass
class AdapterResponse:
    """
    Standardized response envelope from an adapter search invocation.
    Includes execution telemetry and honest coverage diagnostics.
    """
    source_id: str
    hits: List[AdapterHit]
    latency_ms: float
    success: bool
    coverage_notes: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    status_code: int = 200


class SourceAdapter(ABC):
    """
    Abstract interface for all CredenceAI source adapters.
    """
    @property
    @abstractmethod
    def manifest(self) -> AdapterManifest:
        """Returns the static manifest for this adapter."""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        budget: Optional[Dict[str, Any]] = None,
    ) -> AdapterResponse:
        """
        Execute search against the upstream provider under explicit deadlines and budgets.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify upstream provider reachability and status."""
        pass
