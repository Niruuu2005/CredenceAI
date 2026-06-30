from fastapi import Request, Response, BackgroundTasks
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
from app.services.api_key_service import validate_api_key, update_key_last_used


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # If API key auth is disabled, bypass validation
        if not settings.ENABLE_API_KEY_AUTH:
            return await call_next(request)

        # Bypass check for CORS preflight OPTIONS request
        if request.method == "OPTIONS":
            return await call_next(request)

        # Enforce API key only on actual protected API endpoints
        API_PREFIXES = [
            "/jobs", "/goals", "/search", "/agents", "/evidence", "/intelligence", "/verticals",
            "/monitors", "/collections",
            "/api/jobs", "/api/goals", "/api/search", "/api/agents", "/api/evidence",
            "/api/intelligence", "/api/verticals", "/api/monitors", "/api/collections",
        ]
        path = request.url.path
        is_api_route = any(path == prefix or path.startswith(prefix + "/") for prefix in API_PREFIXES)
        if not is_api_route:
            return await call_next(request)

        # Get API key from headers
        api_key = request.headers.get("x-api-key") or request.headers.get("X-API-Key")

        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"error": "missing_api_key", "message": "X-API-Key header is required."}
            )

        if not api_key.startswith("cred_sk_"):
            return JSONResponse(
                status_code=401,
                content={"error": "invalid_api_key_format", "message": "API key format is invalid."}
            )

        # Load SessionLocal dynamically to ensure any test mocking (e.g. from conftest.py) is active
        import app.database as database_module
        db = database_module.SessionLocal()
        try:
            key_record = validate_api_key(db, api_key)
            if not key_record:
                return JSONResponse(
                    status_code=401,
                    content={"error": "invalid_api_key", "message": "Unrecognized or revoked API key."}
                )
            
            # Extract attributes immediately to prevent DetachedInstanceError
            key_id = key_record.id
            key_owner = key_record.owner
            key_user_id = key_record.user_id or key_owner
            
            request.state.api_key_owner = key_owner
            request.state.api_key_user_id = key_user_id
            
            # Call next middleware / route handler
            response = await call_next(request)
            
            # Non-blocking update of last_used_at using BackgroundTasks
            bg = BackgroundTasks()
            bg.add_task(update_key_last_used, key_id)
            response.background = bg
            
            return response
        finally:
            db.close()
