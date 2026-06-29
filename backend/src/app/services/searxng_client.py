import logging
import time
import requests
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class SearXNGClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.SEARXNG_BASE_URL

    def search(self, query: str, categories: Optional[str] = None) -> Dict[str, Any]:
        """Query SearXNG (or mock). Full timing + success/failure logging."""
        t0 = time.perf_counter()

        # ── MOCK MODE ────────────────────────────────────────────────────
        if settings.MOCK_SERVICES:
            result = {
                "query": query,
                "results": [
                    {
                        "title": f"Refinery intelligence result for: {query}",
                        "url": "https://credence-refinery.org/intelligence",
                        "content": f"Simulated intelligence card matching input query: '{query}'",
                        "engine": "mock-adapter",
                    }
                ],
            }
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.info(
                f"SEARXNG  STATUS=MOCK  "
                f"query='{query[:60]}'  "
                f"results=1  source=mock-adapter  "
                f"elapsed={elapsed_ms:.2f}ms"
            )
            return result

        # ── LIVE MODE ────────────────────────────────────────────────────
        url = f"{self.base_url.rstrip('/')}/search"
        params = {"q": query, "format": "json"}
        if categories:
            params["categories"] = categories

        logger.info(
            f"SEARXNG  STATUS=REQUESTING  "
            f"query='{query[:60]}'  "
            f"endpoint={url}  "
            f"categories={categories or 'all'}"
        )

        try:
            response = requests.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            n_results = len(data.get("results", []))
            elapsed_ms = (time.perf_counter() - t0) * 1000
            engines = list({r.get("engine", "unknown") for r in data.get("results", [])})
            logger.info(
                f"SEARXNG  STATUS=SUCCESS  "
                f"query='{query[:60]}'  "
                f"results={n_results}  "
                f"engines={engines}  "
                f"elapsed={elapsed_ms:.2f}ms"
            )
            return data

        except requests.exceptions.Timeout:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.error(
                f"SEARXNG  STATUS=TIMEOUT  "
                f"query='{query[:60]}'  "
                f"endpoint={url}  "
                f"elapsed={elapsed_ms:.2f}ms"
            )
            raise RuntimeError("SearXNG search timed out") from None

        except requests.exceptions.ConnectionError as e:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.warning(
                f"SEARXNG  STATUS=CONNECTION_FAILED  "
                f"query='{query[:60]}'  "
                f"endpoint={url}  "
                f"error='{e}'  "
                f"elapsed={elapsed_ms:.2f}ms. "
                f"Attempting DuckDuckGo Lite crawler fallback..."
            )
            try:
                return self._search_duckduckgo_fallback(query)
            except Exception as fallback_err:
                logger.error(f"SEARXNG_FALLBACK  FAILED  error='{fallback_err}'")
                raise RuntimeError(f"SearXNG connection error and fallback failed: {e}") from e

        except Exception as e:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.error(
                f"SEARXNG  STATUS=FAILED  "
                f"query='{query[:60]}'  "
                f"endpoint={url}  "
                f"error='{e}'  "
                f"elapsed={elapsed_ms:.2f}ms"
            )
            raise RuntimeError(f"SearXNG search failed: {e}") from e

    def _search_duckduckgo_fallback(self, query: str) -> Dict[str, Any]:
        """Fall back to DuckDuckGo Lite scraping to get real search results without Docker."""
        t0 = time.perf_counter()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://lite.duckduckgo.com/"
        }
        try:
            response = requests.post(
                "https://lite.duckduckgo.com/lite/",
                data={"q": query},
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()

            import re
            from html import unescape
            rows = re.findall(r'<tr.*?>(.*?)</tr>', response.text, re.DOTALL)

            results = []
            current_item = {}

            for row in rows:
                if "result-link" in row:
                    link_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', row, re.DOTALL)
                    if link_match:
                        url = link_match.group(1)
                        if "duckduckgo.com/y.js" in url:
                            continue
                        title = re.sub(r'<[^>]+>', '', link_match.group(2))
                        title = unescape(title.strip())
                        if current_item:
                            results.append(current_item)
                        current_item = {
                            "title": title,
                            "url": url,
                            "content": "",
                            "engine": "duckduckgo-lite"
                        }
                elif "result-snippet" in row:
                    snippet = re.sub(r'<[^>]+>', '', row)
                    snippet = unescape(snippet.strip())
                    if current_item:
                        current_item["content"] = snippet
                        results.append(current_item)
                        current_item = {}

            if current_item:
                results.append(current_item)

            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.info(
                f"SEARXNG_FALLBACK  STATUS=SUCCESS  "
                f"query='{query[:60]}'  "
                f"results={len(results)}  "
                f"elapsed={elapsed_ms:.2f}ms"
            )
            return {"query": query, "results": results}
        except Exception as e:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.error(
                f"SEARXNG_FALLBACK  STATUS=FAILED  "
                f"query='{query[:60]}'  "
                f"error='{e}'  "
                f"elapsed={elapsed_ms:.2f}ms"
            )
            raise
