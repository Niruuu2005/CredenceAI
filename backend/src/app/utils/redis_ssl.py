"""Redis / Celery SSL helpers for rediss:// URLs (e.g. Upstash on Render)."""

from __future__ import annotations

import ssl
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

_CERT_REQS_MAP: dict[str, ssl.VerifyMode] = {
    "CERT_REQUIRED": ssl.CERT_REQUIRED,
    "CERT_OPTIONAL": ssl.CERT_OPTIONAL,
    "CERT_NONE": ssl.CERT_NONE,
}


def is_rediss_url(url: str) -> bool:
    return url.startswith("rediss://")


def resolve_ssl_cert_reqs(url: str, default: str = "CERT_REQUIRED") -> ssl.VerifyMode:
    """Read ssl_cert_reqs from URL query string, else use default setting name."""
    parsed = urlparse(url)
    values = parse_qs(parsed.query).get("ssl_cert_reqs")
    if values:
        return _CERT_REQS_MAP.get(values[0].upper(), ssl.CERT_REQUIRED)
    return _CERT_REQS_MAP.get(default.upper(), ssl.CERT_REQUIRED)


def celery_ssl_options(url: str, default_cert_reqs: str = "CERT_REQUIRED") -> dict[str, ssl.VerifyMode]:
    return {"ssl_cert_reqs": resolve_ssl_cert_reqs(url, default_cert_reqs)}


def redis_client_kwargs(url: str, default_cert_reqs: str = "CERT_REQUIRED") -> dict[str, object]:
    if not is_rediss_url(url):
        return {}
    return {
        "ssl": True,
        "ssl_cert_reqs": resolve_ssl_cert_reqs(url, default_cert_reqs),
    }


def ensure_rediss_ssl_query_param(
    url: str,
    default_cert_reqs: str = "CERT_REQUIRED",
) -> str:
    """Append ssl_cert_reqs to rediss:// URLs when missing (required by redis-py/kombu)."""
    if not is_rediss_url(url):
        return url

    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    if "ssl_cert_reqs" in query:
        return url

    cert_name = default_cert_reqs.upper()
    query["ssl_cert_reqs"] = [cert_name]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))
