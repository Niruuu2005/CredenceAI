"""Background self-ping to keep Render free-tier web services warm."""

from __future__ import annotations

import asyncio
import logging
import os

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def resolve_self_keepalive_health_url() -> str | None:
    """Public health URL for outbound self-ping (must hit Render's external URL)."""
    base = (
        os.environ.get("RENDER_EXTERNAL_URL")
        or settings.API_PUBLIC_URL
        or ""
    ).strip().rstrip("/")
    if not base:
        return None
    return f"{base}/api/health"


async def self_keepalive_loop(stop: asyncio.Event) -> None:
    """
    Infinite loop: GET /api/health on this service's public URL, then wait
    SELF_KEEPALIVE_INTERVAL_SEC before the next ping.
    """
    url = resolve_self_keepalive_health_url()
    if not url:
        logger.warning(
            "SELF KEEPALIVE >> disabled — set RENDER_EXTERNAL_URL (auto on Render) "
            "or API_PUBLIC_URL"
        )
        return

    interval = settings.SELF_KEEPALIVE_INTERVAL_SEC
    logger.info("SELF KEEPALIVE >> started url=%s interval=%ds", url, interval)

    while not stop.is_set():
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
            if response.is_success:
                logger.debug("SELF KEEPALIVE >> ping ok status=%s", response.status_code)
            else:
                logger.warning(
                    "SELF KEEPALIVE >> ping non-ok status=%s", response.status_code
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("SELF KEEPALIVE >> ping failed: %s", exc)

        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
            break
        except asyncio.TimeoutError:
            continue

    logger.info("SELF KEEPALIVE >> stopped")


def start_self_keepalive(stop: asyncio.Event) -> asyncio.Task:
    return asyncio.create_task(self_keepalive_loop(stop), name="self_keepalive")
