import logging
from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_JWT_SECRETS = {"", "change-me", "change-me-in-production-1234567890"}


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

    if errors:
        for err in errors:
            logger.error("PRODUCTION CONFIG: %s", err)
        raise RuntimeError("Production configuration validation failed: " + "; ".join(errors))
