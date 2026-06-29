import logging
import requests
import time
from typing import Dict, Any, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Simple in-memory cache for Wikidata responses
_wikidata_cache = {}

# Wikidata requires a proper User-Agent identifying the app:
# https://www.mediawiki.org/wiki/API:Etiquette
_HEADERS = {
    "User-Agent": "CredenceAI/2.0 (https://github.com/Niruuu2005/credenceai-refinery; niruuu2005@example.com) python-requests/2.31"
}

# Rate limiting: track last request time
_last_request_time: float = 0.0
_MIN_REQUEST_INTERVAL = 0.5  # seconds between requests


def _rate_limit():
    """Enforce minimum interval between Wikidata requests to avoid 429/403."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.time()


class WikidataClient:
    """Client for interacting with the Wikidata API.
    
    Uses proper User-Agent headers per Wikidata's API etiquette policy,
    in-memory caching to avoid redundant calls, and rate limiting to
    prevent 403/429 responses.
    """

    BASE_URL = "https://www.wikidata.org/w/api.php"

    def __init__(self):
        self.enabled = settings.ENABLE_WIKIDATA
        self._session = requests.Session()
        self._session.headers.update(_HEADERS)

    def search_entities(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for entities on Wikidata by query string.
        Returns a list of matching entities with IDs, labels, and descriptions.
        """
        if not self.enabled:
            return []

        cache_key = f"search_{query}_{limit}"
        if cache_key in _wikidata_cache:
            logger.debug(f"Wikidata API cache hit for '{query}'")
            return _wikidata_cache[cache_key]

        params = {
            "action": "wbsearchentities",
            "format": "json",
            "language": "en",
            "type": "item",
            "search": query,
            "limit": limit,
        }

        try:
            _rate_limit()
            logger.info(f"Querying Wikidata for: {query}")
            start_time = time.time()
            response = self._session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            elapsed = time.time() - start_time
            logger.debug(f"Wikidata API returned in {elapsed:.2f}s")

            results = data.get("search", [])
            formatted_results = []
            for r in results:
                formatted_results.append(
                    {
                        "wikidata_id": r.get("id"),
                        "canonical_name": r.get("label"),
                        "description": r.get("description"),
                        "concepturi": r.get("concepturi"),
                    }
                )

            _wikidata_cache[cache_key] = formatted_results
            return formatted_results
        except Exception as e:
            logger.error(f"Error querying Wikidata for '{query}': {str(e)}")
            return []

    def get_entity_details(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific Wikidata entity by ID (e.g., Q42).
        Returns structured dict with canonical_name, description, aliases.
        """
        if not self.enabled:
            return None

        cache_key = f"details_{entity_id}"
        if cache_key in _wikidata_cache:
            return _wikidata_cache[cache_key]

        params = {
            "action": "wbgetentities",
            "format": "json",
            "ids": entity_id,
            "languages": "en",
            "props": "labels|descriptions|aliases|sitelinks",
        }

        try:
            _rate_limit()
            response = self._session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            entities = data.get("entities", {})
            if entity_id in entities:
                entity_data = entities[entity_id]

                # Parse aliases
                aliases = []
                if "aliases" in entity_data and "en" in entity_data["aliases"]:
                    aliases = [
                        a.get("value") for a in entity_data["aliases"]["en"]
                    ]

                formatted_data = {
                    "wikidata_id": entity_data.get("id"),
                    "canonical_name": entity_data.get("labels", {})
                    .get("en", {})
                    .get("value"),
                    "description": entity_data.get("descriptions", {})
                    .get("en", {})
                    .get("value"),
                    "aliases": aliases,
                }

                _wikidata_cache[cache_key] = formatted_data
                return formatted_data
            return None
        except Exception as e:
            logger.error(
                f"Error getting details for Wikidata entity '{entity_id}': {str(e)}"
            )
            return None
