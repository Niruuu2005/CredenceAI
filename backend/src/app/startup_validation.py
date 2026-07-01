import logging
from urllib.parse import urlparse

from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_JWT_SECRETS = {"", "change-me", "change-me-in-production-1234567890"}

_LOCALHOST_ORIGIN_PREFIXES = ("http://localhost", "http://127.0.0.1")


def _is_localhost_url(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
        return host in ("localhost", "127.0.0.1", "::1")
    except Exception:
        return False


def _google_oauth_configured() -> bool:
    return bool(
        settings.GOOGLE_CLIENT_ID
        and settings.GOOGLE_CLIENT_SECRET
        and settings.GOOGLE_REDIRECT_URI
    )


def _github_oauth_configured() -> bool:
    return bool(
        settings.GITHUB_CLIENT_ID
        and settings.GITHUB_CLIENT_SECRET
        and settings.GITHUB_REDIRECT_URI
    )


def _is_localhost_only_cors(origins: list[str]) -> bool:
    if not origins:
        return True
    return all(origin.startswith(_LOCALHOST_ORIGIN_PREFIXES) for origin in origins)


def _cors_production_ok() -> bool:
    origins = settings.CORS_ALLOWED_ORIGINS
    if not origins:
        return False
    has_https = any(origin.startswith("https://") for origin in origins)
    return has_https and not _is_localhost_only_cors(origins)


def validate_production_config() -> None:
    if settings.APP_ENV != "production":
        return

    errors = []
    if settings.JWT_SECRET in DEFAULT_JWT_SECRETS:
        errors.append("JWT_SECRET must be set to a strong value in production.")
    if not _google_oauth_configured() and not _github_oauth_configured():
        errors.append(
            "At least one OAuth provider must be configured in production "
            "(Google: GOOGLE_CLIENT_ID/SECRET/REDIRECT_URI or "
            "GitHub: GITHUB_CLIENT_ID/SECRET/REDIRECT_URI)."
        )
    if not _cors_production_ok():
        errors.append(
            "CORS_ALLOWED_ORIGINS must include at least one https:// frontend origin "
            "in production (not localhost-only)."
        )
    if settings.CELERY_ALWAYS_EAGER:
        errors.append(
            "CELERY_ALWAYS_EAGER must be false in production. "
            "Run a separate Celery worker service for background jobs."
        )
    if (
        settings.SEARCH_PROVIDER == "searxng"
        and not settings.MOCK_SERVICES
        and _is_localhost_url(settings.SEARXNG_BASE_URL)
    ):
        errors.append(
            "SEARXNG_BASE_URL cannot point to localhost when SEARCH_PROVIDER=searxng. "
            "Set a deployed SearXNG endpoint or use SEARCH_PROVIDER=duckduckgo."
        )

    if errors:
        for err in errors:
            logger.error("PRODUCTION CONFIG: %s", err)
        raise RuntimeError("Production configuration validation failed: " + "; ".join(errors))

    logger.info(
        "CORS: %d origins configured: %s",
        len(settings.CORS_ALLOWED_ORIGINS),
        ", ".join(settings.CORS_ALLOWED_ORIGINS),
    )
    log_runtime_backends()


def log_runtime_backends() -> None:
    from app.services.backend_selection import (
        resolve_search_backend,
        resolve_storage_backend,
    )
    from app.services.searxng_client import resolve_search_provider

    openai = "yes" if settings.OPENAI_API_KEY else "no"
    celery_mode = "eager" if settings.CELERY_ALWAYS_EAGER else "worker"
    search_provider = resolve_search_provider()

    logger.info(
        "STARTUP >> search_backend=%s storage_backend=%s celery_mode=%s search_provider=%s",
        resolve_search_backend(),
        resolve_storage_backend(),
        celery_mode,
        search_provider,
    )
    if not settings.OPENAI_API_KEY:
        logger.warning(
            "STARTUP >> OPENAI_API_KEY not configured — planner will use search fallback"
        )
    else:
        logger.info("STARTUP >> OPENAI_API_KEY configured=%s", openai)
