import pytest
from unittest.mock import patch, MagicMock
from app.services.wikidata_client import WikidataClient, _wikidata_cache

@pytest.fixture(autouse=True)
def clear_cache():
    _wikidata_cache.clear()
    yield

@patch("app.services.wikidata_client.requests.Session.get")
def test_search_entities(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "search": [
            {"id": "Q42", "label": "Douglas Adams", "description": "English writer and humorist"}
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    client = WikidataClient()
    client.enabled = True
    
    results = client.search_entities("Douglas Adams", limit=1)
    
    assert len(results) == 1
    assert results[0]["wikidata_id"] == "Q42"
    assert results[0]["canonical_name"] == "Douglas Adams"
    mock_get.assert_called_once()

    # Test cache hit
    results2 = client.search_entities("Douglas Adams", limit=1)
    assert len(results2) == 1
    assert mock_get.call_count == 1

@patch("app.services.wikidata_client.requests.Session.get")
def test_get_entity_details(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "entities": {
            "Q42": {
                "id": "Q42",
                "labels": {"en": {"value": "Douglas Adams"}},
                "descriptions": {"en": {"value": "English writer"}}
            }
        }
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    client = WikidataClient()
    client.enabled = True

    details = client.get_entity_details("Q42")
    
    assert details is not None
    assert details["wikidata_id"] == "Q42"
    assert details["canonical_name"] == "Douglas Adams"
    mock_get.assert_called_once()
