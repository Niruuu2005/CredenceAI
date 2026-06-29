"""
Unit tests for PlaywrightCrawler (Sprint 52)

Tests cover:
- Mock mode HTML generation
- Successful URL structure in mock content
- Graceful fallback when playwright is unavailable
- Synchronous .crawl() wrapper
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.playwright_crawler import PlaywrightCrawler
from app.config import settings


@pytest.fixture
def playwright_crawler_mock():
    """PlaywrightCrawler fixture with MOCK_SERVICES=True."""
    with patch.object(settings, "MOCK_SERVICES", True):
        crawler = PlaywrightCrawler()
    return crawler


@pytest.fixture
def playwright_crawler_real():
    """PlaywrightCrawler fixture with MOCK_SERVICES=False."""
    with patch.object(settings, "MOCK_SERVICES", False):
        crawler = PlaywrightCrawler()
    return crawler


# ──────────────────────────────────────────────
# Mock mode tests
# ──────────────────────────────────────────────

def test_mock_mode_returns_html(playwright_crawler_mock):
    """Mock mode should return well-formed HTML."""
    result = playwright_crawler_mock.crawl("https://example.com/page")
    assert isinstance(result, str)
    assert "<html>" in result
    assert "Dynamic Content" in result or "Mock" in result


def test_mock_mode_includes_url(playwright_crawler_mock):
    """Mock mode HTML should contain the requested URL."""
    url = "https://example.com/specific-article"
    result = playwright_crawler_mock.crawl(url)
    assert url in result


def test_mock_mode_has_body_tag(playwright_crawler_mock):
    """Mock result must have a body tag for downstream parsers."""
    result = playwright_crawler_mock.crawl("https://example.com")
    assert "<body>" in result
    assert "</body>" in result


def test_mock_mode_has_title(playwright_crawler_mock):
    """Mock result must have a title tag."""
    result = playwright_crawler_mock.crawl("https://example.com")
    assert "<title>" in result


# ──────────────────────────────────────────────
# Fallback when playwright is not installed
# ──────────────────────────────────────────────

def test_fallback_when_playwright_missing():
    """If playwright library is missing, .crawl() should return fallback HTML."""
    with patch.object(settings, "MOCK_SERVICES", False):
        crawler = PlaywrightCrawler()

    # Patch import of playwright to simulate ImportError
    import builtins
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "playwright.async_api":
            raise ImportError("playwright not installed")
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        result = crawler.crawl("https://example.com")
    # Should not raise; must return a string fallback
    assert isinstance(result, str)
    assert len(result) > 0


# ──────────────────────────────────────────────
# Async internal method via mock
# ──────────────────────────────────────────────

def test_crawl_async_mock_mode():
    """Async _crawl_async in mock mode returns expected HTML."""
    import asyncio
    with patch.object(settings, "MOCK_SERVICES", True):
        crawler = PlaywrightCrawler()

    url = "https://asynctest.com"
    result = asyncio.get_event_loop().run_until_complete(crawler._crawl_async(url))
    assert isinstance(result, str)
    assert url in result


def test_crawl_async_playwright_exception():
    """If async playwright raises, synchronous .crawl() returns fallback HTML."""
    with patch.object(settings, "MOCK_SERVICES", False):
        crawler = PlaywrightCrawler()

    async def failing_crawl(url):
        raise RuntimeError("Simulated browser crash")

    with patch.object(crawler, "_crawl_async", side_effect=failing_crawl):
        result = crawler.crawl("https://example.com")
    assert isinstance(result, str)
    # Must contain fallback content
    assert "failed" in result.lower() or "playwright" in result.lower()
