import pytest
import requests
from unittest.mock import patch, Mock
from app.services.searxng_client import SearXNGClient

def test_searxng_client_success():
    client = SearXNGClient(base_url="http://localhost:8080")
    
    mock_response = Mock()
    mock_response.json.return_value = {"results": [{"title": "Test", "url": "http://example.com"}]}
    mock_response.raise_for_status = Mock()
    
    with patch("requests.get", return_value=mock_response) as mock_get:
        res = client.search("test query")
        assert len(res["results"]) == 1
        assert res["results"][0]["title"] == "Test"
        mock_get.assert_called_once()

def test_searxng_client_timeout():
    client = SearXNGClient(base_url="http://localhost:8080")
    
    with patch("requests.get", side_effect=requests.exceptions.Timeout("Timeout")):
        with pytest.raises(RuntimeError) as exc_info:
            client.search("test query")
        assert "timed out" in str(exc_info.value)
