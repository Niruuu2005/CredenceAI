import logging
import requests
import time
from typing import Dict, Any, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Simple in-memory cache for Wikipedia responses
_wikipedia_cache = {}

class WikipediaClient:
    def __init__(self):
        self.api_url = "https://en.wikipedia.org/w/api.php"
        self.headers = {
            "User-Agent": "CredenceAI/1.0 (contact@credenceai.org; research pipeline)"
        }
        self.enabled = settings.ENABLE_WIKIPEDIA

    def search_pages(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Search Wikipedia pages by query."""
        if not self.enabled:
            logger.info("Wikipedia integration is disabled")
            return []

        cache_key = f"search:{query}:{limit}"
        if cache_key in _wikipedia_cache:
            logger.debug(f"WIKIPEDIA  cache_hit  query='{query}'")
            return _wikipedia_cache[cache_key]

        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json"
        }

        try:
            t0 = time.perf_counter()
            response = requests.get(self.api_url, params=params, headers=self.headers, timeout=5.0)
            response.raise_for_status()
            data = response.json()
            results = data.get("query", {}).get("search", [])
            elapsed = (time.perf_counter() - t0) * 1000
            logger.info(f"WIKIPEDIA  search_query='{query}'  results={len(results)}  elapsed={elapsed:.2f}ms")
            
            _wikipedia_cache[cache_key] = results
            return results
        except Exception as e:
            logger.error(f"WIKIPEDIA  search_failed  query='{query}'  error='{e}'")
            return []

    def get_page_summary(self, title: str) -> Optional[Dict[str, Any]]:
        """Get summary, URL, and categories for a Wikipedia page by title."""
        if not self.enabled:
            return None

        cache_key = f"summary:{title}"
        if cache_key in _wikipedia_cache:
            logger.debug(f"WIKIPEDIA  cache_hit  title='{title}'")
            return _wikipedia_cache[cache_key]

        params = {
            "action": "query",
            "prop": "extracts|categories|info",
            "exintro": 1,
            "explaintext": 1,
            "titles": title,
            "inprop": "url",
            "format": "json",
            "redirects": 1
        }

        try:
            t0 = time.perf_counter()
            response = requests.get(self.api_url, params=params, headers=self.headers, timeout=5.0)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get("query", {}).get("pages", {})
            if not pages:
                return None
                
            page_id = list(pages.keys())[0]
            if page_id == "-1":
                return None
                
            page_data = pages[page_id]
            categories = [c.get("title", "").replace("Category:", "") for c in page_data.get("categories", [])]
            categories = [c for c in categories if not c.startswith("Articles") and not c.startswith("All articles")]

            result = {
                "title": page_data.get("title"),
                "wikipedia_url": page_data.get("fullurl"),
                "description": page_data.get("extract", "").strip(),
                "categories": categories,
                "page_id": page_id
            }
            
            elapsed = (time.perf_counter() - t0) * 1000
            logger.info(f"WIKIPEDIA  get_summary='{title}'  elapsed={elapsed:.2f}ms")
            
            _wikipedia_cache[cache_key] = result
            return result
        except Exception as e:
            logger.error(f"WIKIPEDIA  summary_failed  title='{title}'  error='{e}'")
            return None

    def search_and_get_summary(self, query: str) -> Optional[Dict[str, Any]]:
        """Find the best match on Wikipedia and get its summary."""
        search_results = self.search_pages(query, limit=1)
        if not search_results:
            return None
        title = search_results[0].get("title")
        return self.get_page_summary(title)
