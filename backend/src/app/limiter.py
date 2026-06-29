from slowapi import Limiter
from fastapi import Request
from app.config import settings

def get_api_key_or_ip(request: Request) -> str:
    owner = getattr(request.state, "api_key_owner", None)
    if owner:
        return owner
    return request.client.host if request.client else "127.0.0.1"

limiter = Limiter(
    key_func=get_api_key_or_ip,
    enabled=settings.RATE_LIMIT_ENABLED
)
