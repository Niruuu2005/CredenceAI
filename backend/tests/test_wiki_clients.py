import pytest
from unittest.mock import patch, MagicMock
from app.services.wikipedia_client import WikipediaClient, _wikipedia_cache
from app.services.wikidata_client import WikidataClient, _wikidata_cache


@pytest.fixture(autouse=True)
def clear_caches():
    _wikipedia_cache.clear()
    _wikidata_cache.clear()


def test_wikipedia_client_disabled():
    with patch("app.services.wikipedia_client.settings") as mock_settings:
        mock_settings.ENABLE_WIKIPEDIA = False
        client = WikipediaClient()
        assert not client.enabled
        assert client.search_pages("Python") == []
        assert client.get_page_summary("Python") is None


@patch("app.services.wikipedia_client.requests.get")
def test_wikipedia_client_search_success(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "query": {
            "search": [
                {"title": "Python (programming language)", "snippet": "A popular coding language."}
            ]
        }
    }
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    client = WikipediaClient()
    results = client.search_pages("Python")

    assert len(results) == 1
    assert results[0]["title"] == "Python (programming language)"
    mock_get.assert_called_once()

    # Second call should hit the cache
    results_cached = client.search_pages("Python")
    assert len(results_cached) == 1
    mock_get.assert_called_once()  # Still 1 call


@patch("app.services.wikipedia_client.requests.get")
def test_wikipedia_client_get_summary_success(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "query": {
            "pages": {
                "12345": {
                    "title": "Python",
                    "fullurl": "https://en.wikipedia.org/wiki/Python",
                    "extract": "Python is an interpreted programming language.",
                    "categories": [
                        {"title": "Category:Programming languages"},
                        {"title": "Category:Articles with example code"}
                    ]
                }
            }
        }
    }
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    client = WikipediaClient()
    summary = client.get_page_summary("Python")

    assert summary is not None
    assert summary["title"] == "Python"
    assert summary["wikipedia_url"] == "https://en.wikipedia.org/wiki/Python"
    assert "Programming languages" in summary["categories"]
    assert "Articles with example code" not in summary["categories"]  # filtered


def test_wikidata_client_disabled():
    with patch("app.services.wikidata_client.settings") as mock_settings:
        mock_settings.ENABLE_WIKIDATA = False
        client = WikidataClient()
        assert not client.enabled
        assert client.search_entities("Douglas Adams") == []
        assert client.get_entity_details("Q42") is None


@patch("app.services.wikidata_client.requests.Session.get")
def test_wikidata_client_search_success(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "search": [
            {
                "id": "Q42",
                "label": "Douglas Adams",
                "description": "English writer and humorist",
                "concepturi": "https://www.wikidata.org/wiki/Q42"
            }
        ]
    }
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    client = WikidataClient()
    results = client.search_entities("Douglas Adams", limit=1)

    assert len(results) == 1
    assert results[0]["wikidata_id"] == "Q42"
    assert results[0]["canonical_name"] == "Douglas Adams"
    mock_get.assert_called_once()


@patch("app.services.wikidata_client.requests.Session.get")
def test_wikidata_client_get_details_success(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "entities": {
            "Q42": {
                "id": "Q42",
                "labels": {"en": {"value": "Douglas Adams"}},
                "descriptions": {"en": {"value": "English writer and humorist"}},
                "aliases": {
                    "en": [
                        {"value": "Douglas Noel Adams"},
                        {"value": "DNA"}
                    ]
                }
            }
        }
    }
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    client = WikidataClient()
    details = client.get_entity_details("Q42")

    assert details is not None
    assert details["canonical_name"] == "Douglas Adams"
    assert "Douglas Noel Adams" in details["aliases"]
    assert "DNA" in details["aliases"]
