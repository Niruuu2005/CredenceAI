"""
Provider Health Router for CredenceAI Iteration 0.5 (Sprint 60)

Monitors error rates and connection issues for external source providers
(e.g., SearXNG, Wikipedia, Wikidata) and routes queries dynamically.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Global state for provider health tracking
_PROVIDER_HEALTH_REGISTRY: Dict[str, Dict[str, Any]] = {
    "searxng": {"failures": 0, "status": "healthy", "fallback": "duckduckgo"},
    "wikipedia": {"failures": 0, "status": "healthy", "fallback": "wikidata"},
    "wikidata": {"failures": 0, "status": "healthy", "fallback": None},
    "common_crawl": {"failures": 0, "status": "healthy", "fallback": "searxng"}
}


class HealthRouter:
    """
    Dynamically monitors provider health and routes calls to fallback providers if needed.
    """

    def __init__(self, failure_threshold: int = 3):
        self.threshold = failure_threshold

    def record_result(self, provider: str, success: bool):
        """Record the outcome of a provider request."""
        reg = _PROVIDER_HEALTH_REGISTRY.get(provider.lower())
        if not reg:
            return

        if success:
            reg["failures"] = 0
            reg["status"] = "healthy"
        else:
            reg["failures"] += 1
            if reg["failures"] >= self.threshold:
                reg["status"] = "degraded"
                logger.warning(
                    f"HEALTH_ROUTER  provider={provider}  status=DEGRADED  "
                    f"failures={reg['failures']}  fallback={reg['fallback']}"
                )

    def get_route(self, provider: str) -> str:
        """Get the active route/provider to use, resolving to fallback if unhealthy."""
        provider_lower = provider.lower()
        reg = _PROVIDER_HEALTH_REGISTRY.get(provider_lower)
        if not reg:
            return provider

        if reg["status"] == "degraded" and reg["fallback"]:
            logger.info(f"HEALTH_ROUTER  ROUTE_REDIRECT  from={provider_lower}  to={reg['fallback']}")
            return reg["fallback"]

        return provider_lower

    def get_status_report(self) -> Dict[str, Dict[str, Any]]:
        """Return status of all providers."""
        return _PROVIDER_HEALTH_REGISTRY
