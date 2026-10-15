"""
Acquisition module for CredenceAI 2.0.
Provides policy-gated HTTP fetching with SSRF, DNS rebinding, and size protections.
"""

from app.acquisition.ssrf_guard import validate_url_safe, SSRFViolationError
from app.acquisition.http_fetcher import PolicyHttpFetcher, FetchResult

__all__ = [
    "validate_url_safe",
    "SSRFViolationError",
    "PolicyHttpFetcher",
    "FetchResult",
]
