import logging
import random
import re
import time
from html import unescape
from typing import Any, Dict, Literal, Optional
from urllib.parse import urlparse

import requests

from app.config import settings
from app.services.health_router import HealthRouter

logger = logging.getLogger(__name__)

SearchProviderName = Literal["searxng", "duckduckgo"]

_DDG_LITE_URL = "https://lite.duckduckgo.com/lite/"
_DDG_HTML_URL = "https://html.duckduckgo.com/html/"
_DDG_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}
_DDG_CAPTCHA_MARKERS = (
    "anomaly-modal",
    "bots use duckduckgo",
    "verify you are human",
    "challenge-form",
    "sorry, you have been blocked",
)

_health_router = HealthRouter()


class SearchProviderUnavailable(Exception):
    """Raised when no search provider (SearXNG or DuckDuckGo) is reachable."""


def _is_localhost_url(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
        return host in ("localhost", "127.0.0.1", "::1")
    except Exception:
        return False


def is_ddg_challenge_page(html: str) -> bool:
    """Detect DuckDuckGo CAPTCHA/bot challenge pages."""
    lowered = html.lower()
    return any(marker in lowered for marker in _DDG_CAPTCHA_MARKERS)


def _ddg_timeout() -> tuple[float, float]:
    return (settings.DDG_CONNECT_TIMEOUT, settings.DDG_READ_TIMEOUT)


def _ddg_backoff_seconds(attempt: int) -> float:
    base = 0.5 * (2 ** (attempt - 1))
    return min(base + random.uniform(0, 0.5), 8.0)


def resolve_search_provider(
    provider_setting: str | None = None,
    searxng_base_url: str | None = None,
) -> SearchProviderName:
    """Resolve configured search provider (auto picks SearXNG when URL is non-localhost)."""
    mode = (provider_setting or settings.SEARCH_PROVIDER).lower()
    base_url = searxng_base_url if searxng_base_url is not None else settings.SEARXNG_BASE_URL

    if mode == "duckduckgo":
        return "duckduckgo"
    if mode == "searxng":
        return "searxng"
    # auto
    if base_url and not _is_localhost_url(base_url):
        return "searxng"
    return "duckduckgo"


class SearXNGClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.SEARXNG_BASE_URL

    def _effective_provider(self) -> SearchProviderName:
        return resolve_search_provider(searxng_base_url=self.base_url)

    def search(self, query: str, categories: Optional[str] = None) -> Dict[str, Any]:
        """Query search provider (SearXNG, DuckDuckGo, or mock)."""
        t0 = time.perf_counter()

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
                "SEARCH  STATUS=MOCK  query=%r  results=1  elapsed=%.2fms",
                query[:60],
                elapsed_ms,
            )
            return result

        provider = self._effective_provider()
        logger.info(
            "SEARCH  STATUS=REQUESTING  provider=%s  query=%r",
            provider,
            query[:60],
        )

        if provider == "duckduckgo":
            return self._search_duckduckgo(query, t0)

        return self._search_searxng(query, categories, t0)

    def _search_searxng(
        self,
        query: str,
        categories: Optional[str],
        t0: float,
    ) -> Dict[str, Any]:
        if _is_localhost_url(self.base_url):
            raise SearchProviderUnavailable(
                "SEARCH_PROVIDER=searxng requires a non-localhost SEARXNG_BASE_URL."
            )

        url = f"{self.base_url.rstrip('/')}/search"
        params: Dict[str, str] = {"q": query, "format": "json"}
        if categories:
            params["categories"] = categories

        logger.info(
            "SEARXNG  STATUS=REQUESTING  query=%r  endpoint=%s  categories=%s",
            query[:60],
            url,
            categories or "all",
        )

        try:
            response = requests.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            n_results = len(data.get("results", []))
            elapsed_ms = (time.perf_counter() - t0) * 1000
            engines = list({r.get("engine", "unknown") for r in data.get("results", [])})
            _health_router.record_result("searxng", True)
            logger.info(
                "SEARXNG  STATUS=SUCCESS  query=%r  results=%d  engines=%s  elapsed=%.2fms",
                query[:60],
                n_results,
                engines,
                elapsed_ms,
            )
            return data

        except requests.exceptions.Timeout:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            _health_router.record_result("searxng", False)
            logger.error(
                "SEARXNG  STATUS=TIMEOUT  query=%r  endpoint=%s  elapsed=%.2fms",
                query[:60],
                url,
                elapsed_ms,
            )
            raise SearchProviderUnavailable("SearXNG search timed out") from None

        except requests.exceptions.ConnectionError as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            _health_router.record_result("searxng", False)
            logger.warning(
                "SEARXNG  STATUS=CONNECTION_FAILED  query=%r  endpoint=%s  "
                "error=%r  elapsed=%.2fms  falling back to DuckDuckGo",
                query[:60],
                url,
                exc,
                elapsed_ms,
            )
            try:
                return self._search_duckduckgo(query, time.perf_counter())
            except Exception as fallback_err:
                logger.error("SEARXNG_FALLBACK  FAILED  error=%r", fallback_err)
                raise SearchProviderUnavailable(
                    "Search provider unavailable. Configure SEARXNG_BASE_URL "
                    "or set SEARCH_PROVIDER=duckduckgo."
                ) from exc

        except SearchProviderUnavailable:
            raise

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            _health_router.record_result("searxng", False)
            logger.error(
                "SEARXNG  STATUS=FAILED  query=%r  endpoint=%s  error=%r  elapsed=%.2fms",
                query[:60],
                url,
                exc,
                elapsed_ms,
            )
            raise SearchProviderUnavailable(f"SearXNG search failed: {exc}") from exc

    def _search_duckduckgo_ddgs(self, query: str) -> list[Dict[str, Any]]:
        """Primary DDG path via duckduckgo-search library."""
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS
        except ImportError:
            logger.warning("DUCKDUCKGO  ddgs package not installed; skipping library path")
            return []

        results: list[Dict[str, Any]] = []
        try:
            with DDGS() as ddgs:
                for item in ddgs.text(query, max_results=10):
                    url = item.get("href") or item.get("url") or ""
                    title = item.get("title") or ""
                    body = item.get("body") or item.get("snippet") or ""
                    if not url or not title:
                        continue
                    results.append(
                        {
                            "title": title,
                            "url": url,
                            "content": body,
                            "engine": "duckduckgo-ddgs",
                        }
                    )
        except Exception as exc:
            logger.warning("DUCKDUCKGO  ddgs failed  error=%r", exc)
            return []

        return results

    def _search_duckduckgo_html(self, query: str, t0: float) -> Dict[str, Any]:
        """Fallback DDG path via HTML scraping with retries."""
        last_error: Exception | None = None
        endpoints = (_DDG_LITE_URL, _DDG_HTML_URL)
        max_attempts = settings.DDG_MAX_ATTEMPTS

        for attempt in range(1, max_attempts + 1):
            endpoint = endpoints[(attempt - 1) % len(endpoints)]
            headers = {**_DDG_HEADERS, "Referer": endpoint}
            try:
                response = requests.post(
                    endpoint,
                    data={"q": query},
                    headers=headers,
                    timeout=_ddg_timeout(),
                )
                if response.status_code in (202, 429):
                    logger.warning(
                        "DUCKDUCKGO  STATUS=RATE_LIMITED  attempt=%d  status=%d",
                        attempt,
                        response.status_code,
                    )
                    last_error = SearchProviderUnavailable(
                        f"DuckDuckGo returned HTTP {response.status_code}"
                    )
                    time.sleep(_ddg_backoff_seconds(attempt))
                    continue

                response.raise_for_status()

                if is_ddg_challenge_page(response.text):
                    last_error = SearchProviderUnavailable("DuckDuckGo CAPTCHA/challenge page")
                    logger.warning(
                        "DUCKDUCKGO  STATUS=CHALLENGE  attempt=%d  endpoint=%s",
                        attempt,
                        endpoint,
                    )
                    time.sleep(_ddg_backoff_seconds(attempt))
                    continue

                results = self._parse_duckduckgo_html(response.text, endpoint)
                if not results:
                    last_error = ValueError("DuckDuckGo returned no parseable results")
                    logger.warning(
                        "DUCKDUCKGO  STATUS=EMPTY  attempt=%d  endpoint=%s",
                        attempt,
                        endpoint,
                    )
                    time.sleep(_ddg_backoff_seconds(attempt))
                    continue

                elapsed_ms = (time.perf_counter() - t0) * 1000
                _health_router.record_result("duckduckgo", True)
                logger.info(
                    "DUCKDUCKGO  STATUS=SUCCESS  query=%r  results=%d  "
                    "endpoint=%s  attempt=%d  elapsed=%.2fms  backend=html",
                    query[:60],
                    len(results),
                    endpoint,
                    attempt,
                    elapsed_ms,
                )
                return {"query": query, "results": results}

            except requests.exceptions.RequestException as exc:
                last_error = exc
                logger.warning(
                    "DUCKDUCKGO  STATUS=REQUEST_FAILED  attempt=%d  endpoint=%s  error=%r",
                    attempt,
                    endpoint,
                    exc,
                )
                time.sleep(_ddg_backoff_seconds(attempt))

        raise SearchProviderUnavailable(
            "DuckDuckGo HTML search unavailable after retries."
        ) from last_error

    def _search_duckduckgo(self, query: str, t0: float) -> Dict[str, Any]:
        """Query DuckDuckGo via ddgs library first, then HTML fallback."""
        ddgs_results = self._search_duckduckgo_ddgs(query)
        if ddgs_results:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            _health_router.record_result("duckduckgo", True)
            logger.info(
                "DUCKDUCKGO  STATUS=SUCCESS  query=%r  results=%d  elapsed=%.2fms  backend=ddgs",
                query[:60],
                len(ddgs_results),
                elapsed_ms,
            )
            return {"query": query, "results": ddgs_results}

        try:
            return self._search_duckduckgo_html(query, t0)
        except SearchProviderUnavailable as exc:
            _health_router.record_result("duckduckgo", False)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.error(
                "DUCKDUCKGO  STATUS=FAILED  query=%r  elapsed=%.2fms  error=%r",
                query[:60],
                elapsed_ms,
                exc,
            )
            raise SearchProviderUnavailable(
                "DuckDuckGo search unavailable after retries. Try again later."
            ) from exc

    @staticmethod
    def _parse_duckduckgo_html(html: str, endpoint: str) -> list[Dict[str, Any]]:
        """Parse DuckDuckGo Lite or HTML result pages."""
        if "lite.duckduckgo.com" in endpoint:
            return SearXNGClient._parse_duckduckgo_lite(html)
        return SearXNGClient._parse_duckduckgo_html_results(html)

    @staticmethod
    def _parse_duckduckgo_lite(html: str) -> list[Dict[str, Any]]:
        rows = re.findall(r"<tr.*?>(.*?)</tr>", html, re.DOTALL)
        results: list[Dict[str, Any]] = []
        current_item: Dict[str, Any] = {}

        for row in rows:
            if "result-link" in row:
                link_match = re.search(
                    r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', row, re.DOTALL
                )
                if not link_match:
                    continue
                url = link_match.group(1)
                if "duckduckgo.com/y.js" in url:
                    continue
                title = unescape(re.sub(r"<[^>]+>", "", link_match.group(2)).strip())
                if current_item:
                    results.append(current_item)
                current_item = {
                    "title": title,
                    "url": url,
                    "content": "",
                    "engine": "duckduckgo-lite",
                }
            elif "result-snippet" in row:
                snippet = unescape(re.sub(r"<[^>]+>", "", row).strip())
                if current_item:
                    current_item["content"] = snippet
                    results.append(current_item)
                    current_item = {}

        if current_item:
            results.append(current_item)
        return results

    @staticmethod
    def _parse_duckduckgo_html_results(html: str) -> list[Dict[str, Any]]:
        results: list[Dict[str, Any]] = []
        blocks = re.findall(
            r'<div class="result[^"]*"[^>]*>(.*?)</div>\s*</div>',
            html,
            re.DOTALL,
        )
        if not blocks:
            blocks = re.findall(
                r'<article[^>]*class="[^"]*result[^"]*"[^>]*>(.*?)</article>',
                html,
                re.DOTALL,
            )

        for block in blocks:
            link_match = re.search(
                r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                block,
                re.DOTALL,
            )
            if not link_match:
                link_match = re.search(
                    r'<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', block, re.DOTALL
                )
            if not link_match:
                continue
            url = link_match.group(1)
            if "duckduckgo.com" in url:
                continue
            title = unescape(re.sub(r"<[^>]+>", "", link_match.group(2)).strip())
            snippet_match = re.search(
                r'<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>',
                block,
                re.DOTALL,
            )
            snippet = ""
            if snippet_match:
                snippet = unescape(re.sub(r"<[^>]+>", "", snippet_match.group(1)).strip())
            results.append(
                {
                    "title": title,
                    "url": url,
                    "content": snippet,
                    "engine": "duckduckgo-html",
                }
            )
        return results
