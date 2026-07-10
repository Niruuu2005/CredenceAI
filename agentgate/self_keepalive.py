"""Background self-ping to keep Render free-tier web services warm."""

from __future__ import annotations

import asyncio
import logging

import httpx

from config import PUBLIC_BASE_URL, RENDER_EXTERNAL_URL, SELF_KEEPALIVE_INTERVAL_SEC

logger = logging.getLogger(__name__)

KEEPALIVE_MESSAGE = "hello"


def resolve_public_base() -> str | None:
    base = (RENDER_EXTERNAL_URL or PUBLIC_BASE_URL or "").strip().rstrip("/")
    return base or None


def resolve_demo_hello_url() -> str | None:
    base = resolve_public_base()
    if not base:
        return None
    return f"{base}/demo/hello"


async def self_keepalive_loop(stop: asyncio.Event) -> None:
    """POST /demo/hello to this service's public URL every interval seconds."""
    url = resolve_demo_hello_url()
    if not url:
        logger.warning(
            "SELF KEEPALIVE >> disabled — set RENDER_EXTERNAL_URL or PUBLIC_BASE_URL"
        )
        return

    interval = SELF_KEEPALIVE_INTERVAL_SEC
    payload = {"message": KEEPALIVE_MESSAGE}
    logger.info(
        "SELF KEEPALIVE >> started url=%s interval=%ds payload=%r",
        url,
        interval,
        payload,
    )

    while not stop.is_set():
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
            if response.is_success:
                logger.debug(
                    "SELF KEEPALIVE >> demo hello ok status=%s body=%s",
                    response.status_code,
                    response.text[:120],
                )
            else:
                logger.warning(
                    "SELF KEEPALIVE >> demo hello non-ok status=%s",
                    response.status_code,
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("SELF KEEPALIVE >> demo hello failed: %s", exc)

        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
            break
        except asyncio.TimeoutError:
            continue

    logger.info("SELF KEEPALIVE >> stopped")
