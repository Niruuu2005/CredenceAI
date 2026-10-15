"""
Policy-Gated HTTP Fetcher with SSRF and redirect validation.
Implements FR-006, NFR-009, NFR-010, PRV-01, PRV-02, PRV-03, PRV-04.
"""

import logging
import httpx
from typing import Optional, Dict, Any
from app.acquisition.ssrf_guard import validate_url_safe, SSRFViolationError

logger = logging.getLogger(__name__)

DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
DEFAULT_TIMEOUT_SECONDS = 10.0


class FetchResult:
    def __init__(
        self,
        url: str,
        content_bytes: bytes,
        content_text: str,
        content_type: str,
        status_code: int,
        headers: Dict[str, str],
        latency_ms: float,
    ):
        self.url = url
        self.content_bytes = content_bytes
        self.content_text = content_text
        self.content_type = content_type
        self.status_code = status_code
        self.headers = headers
        self.latency_ms = latency_ms


class PolicyHttpFetcher:
    def __init__(
        self,
        max_bytes: int = DEFAULT_MAX_BYTES,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        self.max_bytes = max_bytes
        self.timeout_seconds = timeout_seconds

    async def fetch(
        self,
        url: str,
        client: Optional[httpx.AsyncClient] = None,
    ) -> FetchResult:
        """
        Safely fetch an external resource with SSRF validation, size ceilings,
        and safe redirect verification.
        """
        # Validate initial URL
        validate_url_safe(url)

        headers = {
            "User-Agent": "CredenceAI-Acquisition/2.0 (+https://credenceai.org/bot; rights-aware)",
            "Accept": "text/html,application/xhtml+xml,application/json,text/plain;q=0.9",
        }

        async def _do_fetch(c: httpx.AsyncClient) -> FetchResult:
            import time
            t0 = time.perf_counter()

            # Follow redirects manually to validate each target against SSRF
            current_url = url
            max_redirects = 5

            for _ in range(max_redirects):
                resp = await c.get(
                    current_url,
                    headers=headers,
                    timeout=self.timeout_seconds,
                    follow_redirects=False,
                )

                if resp.is_redirect:
                    location = resp.headers.get("Location")
                    if not location:
                        break
                    # Re-validate the redirect target against SSRF (PRV-03)
                    target_url = str(resp.url.join(location))
                    validate_url_safe(target_url)
                    current_url = target_url
                    continue

                # Enforce response byte ceiling (PRV-04)
                raw_bytes = resp.content
                if len(raw_bytes) > self.max_bytes:
                    raise ValueError(
                        f"Response size {len(raw_bytes)} bytes exceeds limit of {self.max_bytes} bytes."
                    )

                latency_ms = (time.perf_counter() - t0) * 1000
                content_type = resp.headers.get("Content-Type", "application/octet-stream")

                return FetchResult(
                    url=str(resp.url),
                    content_bytes=raw_bytes,
                    content_text=resp.text[:200000],  # Bounded string representation
                    content_type=content_type,
                    status_code=resp.status_code,
                    headers=dict(resp.headers),
                    latency_ms=latency_ms,
                )

            raise ValueError("Too many redirects encountered.")

        if client:
            return await _do_fetch(client)
        else:
            async with httpx.AsyncClient() as new_client:
                return await _do_fetch(new_client)
