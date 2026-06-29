import pytest
from unittest.mock import patch, MagicMock
from app.services.wikipedia_client import WikipediaClient, _wikipedia_cache

@pytest.fixture(autouse=True)
def clear_cache():
    _wikipedia_cache.clear()
    yield

@patch("app.services.wikipedia_client.requests.get")
def test_search_pages(mock_get):
    client = WikipediaClient()
    client.enabled = True
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "query": {
            "search": [
                {"title": "Test Entity", "pageid": 12345, "snippet": "A test entity"}
            ]
        }
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    results = client.search_pages("Test", limit=1)
    
    assert len(results) == 1
    assert results[0]["title"] == "Test Entity"
    mock_get.assert_called_once()

    # Test cache hit
    results2 = client.search_pages("Test", limit=1)
    assert len(results2) == 1
    assert mock_get.call_count == 1  # Should not have called requests.get again

@patch("app.services.wikipedia_client.requests.get")
def test_get_page_summary(mock_get):
    client = WikipediaClient()
    client.enabled = True
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "query": {
            "pages": {
                "12345": {
                    "pageid": 12345,
                    "title": "Test Entity",
                    "extract": "A test entity extract",
                    "fullurl": "https://en.wikipedia.org/wiki/Test_Entity",
                    "categories": [{"title": "Category:Testing"}]
                }
            }
        }
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    details = client.get_page_summary("Test Entity")
    
    assert details is not None
    assert details["title"] == "Test Entity"
    assert details["description"] == "A test entity extract"
    assert details["wikipedia_url"] == "https://en.wikipedia.org/wiki/Test_Entity"
    assert "Testing" in details["categories"]
    mock_get.assert_called_once()
