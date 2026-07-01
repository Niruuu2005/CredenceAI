import re

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

_VERCEL_ORIGIN_RE = re.compile(r"https://.*\.vercel\.app$")

CORS_ALLOW_METHODS = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
CORS_ALLOW_HEADERS = "Content-Type, Authorization"


def _origin_allowed(origin: str) -> bool:
    if origin in settings.CORS_ALLOWED_ORIGINS:
        return True
    return bool(_VERCEL_ORIGIN_RE.fullmatch(origin))


def apply_cors_headers(response, origin: str) -> None:
    """Attach full CORS headers for an allowed origin (used on error responses)."""
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = CORS_ALLOW_METHODS
    response.headers["Access-Control-Allow-Headers"] = CORS_ALLOW_HEADERS


class CorsGuardMiddleware(BaseHTTPMiddleware):
    """Ensure ACAO is present on error responses when CORSMiddleware misses them."""

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        response = await call_next(request)
        if (
            origin
            and _origin_allowed(origin)
            and "access-control-allow-origin" not in response.headers
        ):
            apply_cors_headers(response, origin)
        return response
