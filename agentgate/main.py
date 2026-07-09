"""AgentGate — Pre-action decision API for autonomous agents."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

from config import (
    LLM_ENABLED,
    OPENROUTER_API_KEY,
    PUBLIC_BASE_URL,
    RENDER_EXTERNAL_URL,
    SELF_KEEPALIVE_ENABLED,
    SERVICE_NAME,
    SERVICE_VERSION,
)
from llm_client import compare_options, evaluate_task
from models import (
    CompareOptionsRequest,
    CompareOptionsResponse,
    EvaluateTaskRequest,
    EvaluateTaskResponse,
    HealthResponse,
)
from self_keepalive import self_keepalive_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SKILL_PATH = Path(__file__).resolve().parent / "SKILL.md"


def _base_url() -> str:
    return (PUBLIC_BASE_URL or RENDER_EXTERNAL_URL or "https://YOUR_DEPLOYED_SERVICE_URL").rstrip("/")


def load_skill_markdown() -> str:
    raw = SKILL_PATH.read_text(encoding="utf-8")
    return raw.replace("https://YOUR_DEPLOYED_SERVICE_URL", _base_url())


@asynccontextmanager
async def lifespan(app: FastAPI):
    stop = asyncio.Event()
    task = None
    if SELF_KEEPALIVE_ENABLED:
        task = asyncio.create_task(self_keepalive_loop(stop))
    yield
    stop.set()
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="AgentGate",
    description="Pre-action decision API for autonomous agents",
    version=SERVICE_VERSION,
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    llm_mode = (
        "rules_with_openrouter_fallback"
        if LLM_ENABLED and OPENROUTER_API_KEY
        else "rules_only"
    )
    return HealthResponse(
        status="ok",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        llm_mode=llm_mode,
    )


@app.post("/evaluate-task", response_model=EvaluateTaskResponse)
async def evaluate_task_endpoint(body: EvaluateTaskRequest) -> EvaluateTaskResponse:
    try:
        return await evaluate_task(body)
    except Exception as exc:
        logger.exception("evaluate-task failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.post("/compare-options", response_model=CompareOptionsResponse)
async def compare_options_endpoint(body: CompareOptionsRequest) -> CompareOptionsResponse:
    try:
        return await compare_options(body)
    except Exception as exc:
        logger.exception("compare-options failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.get("/skill.md", response_class=PlainTextResponse)
async def skill_md() -> PlainTextResponse:
    if not SKILL_PATH.exists():
        raise HTTPException(status_code=404, detail="SKILL.md not found")
    return PlainTextResponse(load_skill_markdown(), media_type="text/markdown")
