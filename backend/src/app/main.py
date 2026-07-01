import os
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
from app.logging_config import setup_logging
from app.api.middleware import TraceIdMiddleware
from app.middleware.api_key_auth import ApiKeyMiddleware
from app.middleware.cors_guard import CorsGuardMiddleware
from app.api import jobs, search, health, agents, evidence, intelligence, verticals, goals, auth, monitors, collections, billing, admin
from slowapi.errors import RateLimitExceeded
from app.limiter import limiter

setup_logging()
logger = logging.getLogger(__name__)

CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS = ["Content-Type", "Authorization"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.startup_validation import validate_production_config
    validate_production_config()

    if settings.APP_ENV in ("local", "test"):
        from app.models import Base
        from app.database import engine
        logger.info("STARTUP >> creating database tables (dev/test only)")
        Base.metadata.create_all(bind=engine)
    else:
        logger.info("STARTUP >> production mode — schema managed by Alembic migrations")

    logger.info("STARTUP OK")

    try:
        from app.services.search_index import SearchIndexClient
        logger.info("STARTUP >> warming up search index client")
        SearchIndexClient()
    except Exception as e:
        logger.warning(f"STARTUP >> search index client warmup failed: {e}")

    keepalive_stop = asyncio.Event()
    keepalive_task: asyncio.Task | None = None
    if settings.SELF_KEEPALIVE_ENABLED:
        from app.services.self_keepalive import start_self_keepalive

        keepalive_task = start_self_keepalive(keepalive_stop)

    yield

    if keepalive_task is not None:
        keepalive_stop.set()
        keepalive_task.cancel()
        try:
            await keepalive_task
        except asyncio.CancelledError:
            pass

    logger.info("SHUTDOWN >> CredenceAI shutting down gracefully")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self';"
        )

        if settings.APP_ENV == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


app = FastAPI(
    title="CredenceAI",
    description="AI-assisted search intelligence platform",
    version="0.5.0",
    lifespan=lifespan,
    docs_url=None if settings.APP_ENV == "production" else "/docs",
    redoc_url=None if settings.APP_ENV == "production" else "/redoc",
    openapi_url=None if settings.APP_ENV == "production" else "/openapi.json",
)

app.state.limiter = limiter

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(ApiKeyMiddleware)
app.add_middleware(TraceIdMiddleware)

# CORS must be outermost so preflight OPTIONS is answered before auth/routes.
app.add_middleware(CorsGuardMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
    expose_headers=["X-Trace-Id"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    trace_id = getattr(request.state, "trace_id", None)

    safe_details = []
    for err in exc.errors():
        err_copy = dict(err)
        if "ctx" in err_copy and isinstance(err_copy["ctx"], dict):
            err_copy["ctx"] = {
                k: str(v) if isinstance(v, Exception) else v
                for k, v in err_copy["ctx"].items()
            }
        safe_details.append(err_copy)

    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Request validation failed.",
            "trace_id": trace_id,
            "details": safe_details,
        }
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    trace_id = getattr(request.state, "trace_id", None)
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": f"Too many requests. Limit exceeded: {exc.detail}",
            "trace_id": trace_id
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", None)
    logger.exception(f"Unhandled exception occurred. Trace ID: {trace_id}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An unexpected error occurred.",
            "trace_id": trace_id,
        }
    )


app.include_router(auth.router)
app.include_router(auth.router, prefix="/api")

app.include_router(jobs.router)
app.include_router(goals.router)
app.include_router(search.router)
app.include_router(health.router)
app.include_router(agents.router)
app.include_router(evidence.router)
app.include_router(intelligence.router)
app.include_router(verticals.router)
app.include_router(monitors.router)
app.include_router(collections.router)
app.include_router(billing.router)
app.include_router(admin.router)

app.include_router(jobs.router, prefix="/api")
app.include_router(goals.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(evidence.router, prefix="/api")
app.include_router(intelligence.router, prefix="/api")
app.include_router(verticals.router, prefix="/api")
app.include_router(monitors.router, prefix="/api")
app.include_router(collections.router, prefix="/api")
app.include_router(billing.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/")
def read_root():
    return {
        "message": "Welcome to CredenceAI API.",
        "docs": "/docs",
        "dashboard": "/dashboard",
        "health": "/api/health",
    }


@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    template_path = os.path.join(
        os.path.dirname(__file__), "templates", "dashboard.html"
    )
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()
