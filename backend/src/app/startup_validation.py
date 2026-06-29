import logging
from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_JWT_SECRETS = {"", "change-me", "change-me-in-production-1234567890"}


def validate_production_config() -> None:
    if settings.APP_ENV != "production":
        return

    errors = []
    if settings.JWT_SECRET in DEFAULT_JWT_SECRETS:
        errors.append("JWT_SECRET must be set to a strong value in production.")
    if not settings.GOOGLE_CLIENT_ID:
        errors.append("GOOGLE_CLIENT_ID is required in production.")
    if not settings.GOOGLE_CLIENT_SECRET:
        errors.append("GOOGLE_CLIENT_SECRET is required in production.")
    if not settings.GOOGLE_REDIRECT_URI:
        errors.append("GOOGLE_REDIRECT_URI is required in production.")

    if errors:
        for err in errors:
            logger.error("PRODUCTION CONFIG: %s", err)
        raise RuntimeError("Production configuration validation failed: " + "; ".join(errors))
