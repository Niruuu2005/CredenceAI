"""
Central source adapter registry.
Implements FR-004, SRC-01, SRC-03, SRC-07.
"""

from typing import Dict, List, Optional
import logging
from app.sources.protocol import SourceAdapter, SourceClass, Capability, AdapterManifest

logger = logging.getLogger(__name__)


class SourceRegistry:
    """
    Central registry for source adapters with capability-aware filtering.
    Guarantees no phantom providers are executed.
    """
    def __init__(self):
        self._adapters: Dict[str, SourceAdapter] = {}
        self._health_status: Dict[str, bool] = {}

    def register(self, adapter: SourceAdapter) -> None:
        manifest = adapter.manifest
        self._adapters[manifest.source_id] = adapter
        self._health_status[manifest.source_id] = True
        logger.info(
            f"Registered SourceAdapter '{manifest.source_id}' "
            f"class={manifest.source_class.value} enabled={manifest.enabled} executable={manifest.executable}"
        )

    def get(self, source_id: str) -> Optional[SourceAdapter]:
        return self._adapters.get(source_id)

    def list_all(self) -> List[SourceAdapter]:
        return list(self._adapters.values())

    def list_manifests(self) -> List[AdapterManifest]:
        return [adapter.manifest for adapter in self._adapters.values()]

    def list_executable(
        self,
        source_class: Optional[SourceClass] = None,
        capability: Optional[Capability] = None,
    ) -> List[SourceAdapter]:
        """
        Filter adapters that are configured, enabled, executable, and healthy.
        """
        results = []
        for adapter in self._adapters.values():
            m = adapter.manifest
            if not m.enabled or not m.executable:
                continue
            if not self._health_status.get(m.source_id, False):
                continue
            if source_class and m.source_class != source_class:
                continue
            if capability and capability not in m.capabilities:
                continue
            results.append(adapter)
        return results

    def set_health(self, source_id: str, is_healthy: bool) -> None:
        if source_id in self._adapters:
            self._health_status[source_id] = is_healthy
            logger.info(f"SourceAdapter '{source_id}' health updated: healthy={is_healthy}")


# Global singleton registry
source_registry = SourceRegistry()
