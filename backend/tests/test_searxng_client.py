import pytest
import requests
from unittest.mock import patch, Mock

from app.config import settings
from app.services.searxng_client import (
    SearXNGClient,
    SearchProviderUnavailable,
    resolve_search_provider,
    is_ddg_challenge_page,
)


def test_is_ddg_challenge_page_detects_captcha():
    assert is_ddg_challenge_page("<html><body>Verify you are human</body></html>")
    assert not is_ddg_challenge_page("<html><tr class='result-link'>ok</tr></html>")


def test_searxng_client_duckduckgo_uses_ddgs_when_available():
    original = settings.SEARCH_PROVIDER
    settings.SEARCH_PROVIDER = "duckduckgo"
    client = SearXNGClient(base_url="http://localhost:8080")

    ddgs_results = [
        {
            "title": "DDGS Result",
            "url": "https://example.com/ddgs",
            "content": "snippet",
            "engine": "duckduckgo-ddgs",
        }
    ]

    try:
        with patch.object(client, "_search_duckduckgo_ddgs", return_value=ddgs_results):
            with patch("requests.post") as mock_post:
                res = client.search("test query")
                assert len(res["results"]) == 1
                assert res["results"][0]["engine"] == "duckduckgo-ddgs"
                mock_post.assert_not_called()
    finally:
        settings.SEARCH_PROVIDER = original


def test_searxng_client_duckduckgo_html_skips_challenge_page():
    original = settings.SEARCH_PROVIDER
    settings.SEARCH_PROVIDER = "duckduckgo"
    settings.DDG_MAX_ATTEMPTS = 2
    client = SearXNGClient(base_url="http://localhost:8080")

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "<html>Verify you are human</html>"
    mock_response.raise_for_status = Mock()

    try:
        with patch.object(client, "_search_duckduckgo_ddgs", return_value=[]):
            with patch("requests.post", return_value=mock_response):
                with pytest.raises(SearchProviderUnavailable):
                    client.search("test query")
    finally:
        settings.SEARCH_PROVIDER = original
        settings.DDG_MAX_ATTEMPTS = 6


def test_resolve_search_provider_auto_localhost_uses_duckduckgo():
    assert resolve_search_provider("auto", "http://localhost:8080") == "duckduckgo"


def test_resolve_search_provider_auto_remote_uses_searxng():
    assert (
        resolve_search_provider("auto", "https://searxng.example.com") == "searxng"
    )


def test_resolve_search_provider_explicit():
    assert resolve_search_provider("duckduckgo", "http://localhost:8080") == "duckduckgo"
    assert resolve_search_provider("searxng", "http://localhost:8080") == "searxng"


def test_searxng_client_success_with_searxng_provider():
    original = settings.SEARCH_PROVIDER
    settings.SEARCH_PROVIDER = "searxng"
    client = SearXNGClient(base_url="https://searxng.example.com")

    mock_response = Mock()
    mock_response.json.return_value = {
        "results": [{"title": "Test", "url": "http://example.com"}]
    }
    mock_response.raise_for_status = Mock()

    try:
        with patch("requests.get", return_value=mock_response) as mock_get:
            res = client.search("test query")
            assert len(res["results"]) == 1
            assert res["results"][0]["title"] == "Test"
            mock_get.assert_called_once()
    finally:
        settings.SEARCH_PROVIDER = original


def test_searxng_client_duckduckgo_provider_skips_searxng():
    original = settings.SEARCH_PROVIDER
    settings.SEARCH_PROVIDER = "duckduckgo"
    client = SearXNGClient(base_url="http://localhost:8080")

    ddg_html = """
    <tr><td class="result-link">
    <a href="https://example.com">Example Title</a></td></tr>
    <tr><td class="result-snippet">Example snippet text</td></tr>
    """

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = ddg_html
    mock_response.raise_for_status = Mock()

    try:
        with patch("requests.get") as mock_get:
            with patch("requests.post", return_value=mock_response) as mock_post:
                res = client.search("test query")
                assert len(res["results"]) == 1
                assert res["results"][0]["title"] == "Example Title"
                assert res["results"][0]["url"] == "https://example.com"
                mock_get.assert_not_called()
                mock_post.assert_called()
    finally:
        settings.SEARCH_PROVIDER = original


def test_searxng_client_timeout():
    original = settings.SEARCH_PROVIDER
    settings.SEARCH_PROVIDER = "searxng"
    client = SearXNGClient(base_url="https://searxng.example.com")

    try:
        with patch("requests.get", side_effect=requests.exceptions.Timeout("Timeout")):
            with pytest.raises(SearchProviderUnavailable) as exc_info:
                client.search("test query")
            assert "timed out" in str(exc_info.value)
    finally:
        settings.SEARCH_PROVIDER = original


def test_searxng_client_instantiation_never_raises_on_localhost():
    from app.config import settings

    original = settings.APP_ENV, settings.MOCK_SERVICES, settings.SEARCH_PROVIDER
    settings.APP_ENV = "production"
    settings.MOCK_SERVICES = False
    settings.SEARCH_PROVIDER = "duckduckgo"
    try:
        client = SearXNGClient(base_url="http://localhost:8080")
        assert client.base_url == "http://localhost:8080"
    finally:
        settings.APP_ENV, settings.MOCK_SERVICES, settings.SEARCH_PROVIDER = original


def test_searxng_provider_requires_non_localhost_url():
    original = settings.SEARCH_PROVIDER
    settings.SEARCH_PROVIDER = "searxng"
    client = SearXNGClient(base_url="http://localhost:8080")
    try:
        with pytest.raises(SearchProviderUnavailable, match="non-localhost"):
            client.search("test query")
    finally:
        settings.SEARCH_PROVIDER = original
