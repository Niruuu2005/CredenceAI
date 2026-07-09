"""Background self-ping to keep Render free-tier web services warm."""

from __future__ import annotations

import asyncio
import logging

import httpx

from config import PUBLIC_BASE_URL, RENDER_EXTERNAL_URL, SELF_KEEPALIVE_INTERVAL_SEC

logger = logging.getLogger(__name__)


def resolve_health_url() -> str | None:
    base = (RENDER_EXTERNAL_URL or PUBLIC_BASE_URL or "").strip().rstrip("/")
    if not base:
        return None
    return f"{base}/health"


async def self_keepalive_loop(stop: asyncio.Event) -> None:
    url = resolve_health_url()
    if not url:
        logger.warning(
            "SELF KEEPALIVE >> disabled — set RENDER_EXTERNAL_URL or PUBLIC_BASE_URL"
        )
        return

    interval = SELF_KEEPALIVE_INTERVAL_SEC
    logger.info("SELF KEEPALIVE >> started url=%s interval=%ds", url, interval)

    while not stop.is_set():
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
            if response.is_success:
                logger.debug("SELF KEEPALIVE >> ping ok status=%s", response.status_code)
            else:
                logger.warning("SELF KEEPALIVE >> ping non-ok status=%s", response.status_code)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("SELF KEEPALIVE >> ping failed: %s", exc)

        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
            break
        except asyncio.TimeoutError:
            continue
