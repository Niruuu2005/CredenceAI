"""Resolve search and storage backends from settings (production-safe defaults)."""

from urllib.parse import urlparse

from app.config import settings

SearchBackend = str  # "opensearch" | "database"
StorageBackend = str  # "s3" | "local"


def _is_localhost_url(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
        return host in ("localhost", "127.0.0.1", "::1")
    except Exception:
        return False


def resolve_search_backend() -> SearchBackend:
    mode = settings.SEARCH_BACKEND.lower()
    if mode == "database":
        return "database"
    if mode == "opensearch":
        return "opensearch"
    # auto
    if settings.MOCK_SERVICES:
        return "database"
    if settings.APP_ENV == "production" and _is_localhost_url(settings.OPENSEARCH_URL):
        return "database"
    return "opensearch"


def resolve_storage_backend() -> StorageBackend:
    mode = settings.STORAGE_BACKEND.lower()
    if mode == "local":
        return "local"
    if mode == "s3":
        return "s3"
    # auto
    if settings.MOCK_SERVICES:
        return "local"
    if settings.APP_ENV == "production" and _is_localhost_url(settings.MINIO_ENDPOINT):
        return "local"
    return "s3"


def search_backend_label() -> str:
    return "opensearch" if resolve_search_backend() == "opensearch" else "database_fallback"


def storage_backend_label() -> str:
    return "s3_ok" if resolve_storage_backend() == "s3" else "local_fallback"
