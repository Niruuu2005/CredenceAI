"""
Unit tests for CommonCrawlClient (Sprint 52)

Tests cover:
- CDX lookup in mock mode (success and not-found)
- WARC record fetch in mock mode
- End-to-end fetch_historical_page in mock mode
- Graceful failure when live CDX is unavailable
"""

import pytest
import json
import gzip
import io
from unittest.mock import patch, MagicMock
from app.services.common_crawl_client import CommonCrawlClient
from app.config import settings


@pytest.fixture
def cc_mock():
    """CommonCrawlClient fixture with MOCK_SERVICES=True."""
    with patch.object(settings, "MOCK_SERVICES", True):
        client = CommonCrawlClient()
    return client


@pytest.fixture
def cc_real():
    """CommonCrawlClient fixture with MOCK_SERVICES=False."""
    with patch.object(settings, "MOCK_SERVICES", False):
        client = CommonCrawlClient()
    return client


# ──────────────────────────────────────────────
# CDX Index lookup (mock mode)
# ──────────────────────────────────────────────

def test_lookup_index_mock_success(cc_mock):
    """Mock mode returns a valid WARC record dict."""
    record = cc_mock.lookup_index("https://example.com/article")
    assert record is not None
    assert "warc_filename" in record
    assert "offset" in record
    assert "length" in record
    assert "status" in record


def test_lookup_index_mock_failure_url(cc_mock):
    """Mock mode returns None for URLs containing 'fail' or 'error'."""
    result = cc_mock.lookup_index("https://example.com/fail-page")
    assert result is None

    result = cc_mock.lookup_index("https://example.com/error-endpoint")
    assert result is None


def test_lookup_index_record_has_status_200(cc_mock):
    """Mock CDX record should have HTTP 200 status."""
    record = cc_mock.lookup_index("https://valid-site.com/content")
    assert record["status"] == "200"


# ──────────────────────────────────────────────
# WARC record fetch (mock mode)
# ──────────────────────────────────────────────

def test_fetch_warc_record_mock(cc_mock):
    """Mock WARC fetch returns HTML string."""
    html = cc_mock.fetch_warc_record("crawl-data/test.warc.gz", 0, 100)
    assert isinstance(html, str)
    assert "<html>" in html


def test_fetch_warc_record_mock_contains_content(cc_mock):
    """Mock WARC content contains expected test content."""
    html = cc_mock.fetch_warc_record("crawl-data/test.warc.gz", 5000, 1200)
    assert "CC Archive" in html or "Common Crawl" in html


# ──────────────────────────────────────────────
# End-to-end fetch_historical_page (mock mode)
# ──────────────────────────────────────────────

def test_fetch_historical_page_mock_success(cc_mock):
    """Full pipeline returns HTML for valid URL in mock mode."""
    html = cc_mock.fetch_historical_page("https://example.com/valid-page")
    assert html is not None
    assert isinstance(html, str)
    assert "<html>" in html


def test_fetch_historical_page_mock_not_found(cc_mock):
    """Full pipeline returns None for a URL that would not be indexed."""
    result = cc_mock.fetch_historical_page("https://example.com/fail")
    assert result is None


# ──────────────────────────────────────────────
# Live CDX lookup fallback (network failure)
# ──────────────────────────────────────────────

def test_lookup_index_network_failure(cc_real):
    """If the live CDX server is unreachable, lookup_index returns None gracefully."""
    import requests
    with patch("requests.get", side_effect=requests.exceptions.ConnectionError("Network down")):
        result = cc_real.lookup_index("https://example.com/page")
    assert result is None


def test_fetch_warc_network_failure(cc_real):
    """If WARC fetch fails, fetch_warc_record raises RuntimeError."""
    import requests
    with patch("requests.get", side_effect=requests.exceptions.Timeout("Timeout")):
        with pytest.raises(RuntimeError) as exc_info:
            cc_real.fetch_warc_record("crawl-data/test.warc.gz", 0, 100)
    assert "Failed to fetch" in str(exc_info.value)


def test_fetch_historical_page_live_cdx_response(cc_real):
    """Simulate a successful CDX JSON response and WARC mock fetch."""
    # Build a mock WARC gzip byte stream
    html_content = b"<html><head></head><body><h1>Test</h1></body></html>"
    warc_headers = b"WARC/1.0\r\nContent-Length: 50\r\n\r\nHTTP/1.1 200 OK\r\n\r\n"
    warc_bytes = warc_headers + html_content

    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
        gz.write(warc_bytes)
    compressed = buf.getvalue()

    cdx_response = MagicMock()
    cdx_response.status_code = 200
    cdx_response.text = json.dumps({
        "warc_filename": "crawl-data/CC-MAIN-2023-50/test.warc.gz",
        "offset": "0",
        "length": str(len(compressed)),
        "status": "200",
        "mime": "text/html"
    })

    warc_response = MagicMock()
    warc_response.status_code = 206
    warc_response.content = compressed
    warc_response.raise_for_status = MagicMock()

    with patch("requests.get", side_effect=[cdx_response, warc_response]):
        result = cc_real.fetch_historical_page("https://example.com/live-test")

    assert result is not None
    assert "Test" in result or "<html>" in result
