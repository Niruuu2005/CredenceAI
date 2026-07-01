import re

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

_VERCEL_ORIGIN_RE = re.compile(r"https://.*\.vercel\.app$")


def _origin_allowed(origin: str) -> bool:
    if origin in settings.CORS_ALLOWED_ORIGINS:
        return True
    return bool(_VERCEL_ORIGIN_RE.fullmatch(origin))


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
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        return response
