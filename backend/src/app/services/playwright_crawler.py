"""
Playwright Crawler Fallback for CredenceAI Iteration 0.3

Launches a headless browser instance to render JS-heavy websites when static crawls fail.
Includes a mock fallback mode when MOCK_SERVICES=True or if playwright is missing.
"""

import logging
import asyncio
import os
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

class PlaywrightCrawler:
    """
    Playwright-backed browser fetcher for rendering JS-rendered elements.
    Uses dynamic browser launch parameters and a mock handler for development.
    """

    def __init__(self):
        self.timeout_ms = 15000  # 15 seconds deadline
        self.mock_mode = settings.MOCK_SERVICES

    async def _crawl_async(self, url: str) -> str:
        """Asynchronous execution of Playwright browser lookup."""
        if self.mock_mode:
            logger.info(f"PLAYWRIGHT_CRAWLER  MOCK_MODE  url={url}")
            return f"<html><head><title>Mocked Playwright Page</title></head><body><h1>Dynamic Content</h1><p>Mock dynamic content parsed via browser rendering for {url}</p></body></html>"

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.warning("Playwright library is not installed. Falling back to mock rendered html.")
            return f"<html><body><p>Playwright not installed. Mocked fallback for {url}</p></body></html>"

        logger.info(f"PLAYWRIGHT_CRAWLER  START_BROWSER  url={url}")
        
        try:
            async with async_playwright() as p:
                # Launch headless browser (Chromium)
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
                )
                try:
                    context = await browser.new_context(
                        viewport={"width": 1280, "height": 800},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                    page = await context.new_page()
                    
                    # Navigate and wait until network is idle or load event fires
                    await page.goto(url, timeout=self.timeout_ms, wait_until="load")
                    
                    # Optional: wait extra time to let JS render
                    await asyncio.sleep(1.0)
                    
                    html_content = await page.content()
                    logger.info(f"PLAYWRIGHT_CRAWLER  SUCCESS  url={url}  length={len(html_content)}")
                    return html_content
                finally:
                    await browser.close()
        except Exception as e:
            logger.error(f"PLAYWRIGHT_CRAWLER  FAILED  url={url}  error='{e}'")
            raise RuntimeError(f"Playwright crawl failed: {str(e)}") from e

    def crawl(self, url: str) -> str:
        """
        Synchronous interface wrapper for Celery integration.
        Executes the async browser crawl using an event loop.
        """
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            if loop.is_running():
                # If loop is already running (e.g. inside an async context), execute task in future
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(self._crawl_async(url))
            else:
                return loop.run_until_complete(self._crawl_async(url))
        except Exception as e:
            logger.error(f"PLAYWRIGHT_CRAWLER  LOOP_ERROR  url={url}  error='{e}'")
            # If everything fails, return basic fallback
            return f"<html><body><p>Playwright crawl failed: {str(e)}</p></body></html>"
