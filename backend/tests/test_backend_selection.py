"""Tests for search/storage backend selection on Render production."""

import pytest

from app.config import settings
from app.services import search_index, storage
from app.services.backend_selection import (
    resolve_search_backend,
    resolve_storage_backend,
    search_backend_label,
    storage_backend_label,
)
from app.services.search_index import SearchIndexClient
from app.services.storage import StorageClient


@pytest.fixture(autouse=True)
def reset_client_singletons():
    search_index._opensearch_available = None
    search_index._cached_opensearch_client = None
    storage._s3_available = None
    storage._cached_client = None
    yield
    search_index._opensearch_available = None
    search_index._cached_opensearch_client = None
    storage._s3_available = None
    storage._cached_client = None


def test_resolve_search_database_explicit():
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(settings, "SEARCH_BACKEND", "database")
        assert resolve_search_backend() == "database"
        assert search_backend_label() == "database_fallback"


def test_resolve_storage_local_explicit():
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(settings, "STORAGE_BACKEND", "local")
        assert resolve_storage_backend() == "local"
        assert storage_backend_label() == "local_fallback"


def test_production_localhost_opensearch_skips_probe():
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(settings, "APP_ENV", "production")
        mp.setattr(settings, "SEARCH_BACKEND", "auto")
        mp.setattr(settings, "OPENSEARCH_URL", "http://localhost:9200")
        mp.setattr(settings, "MOCK_SERVICES", False)
        assert resolve_search_backend() == "database"
        client = SearchIndexClient()
        assert client.use_opensearch is False


def test_production_localhost_minio_skips_probe():
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(settings, "APP_ENV", "production")
        mp.setattr(settings, "STORAGE_BACKEND", "auto")
        mp.setattr(settings, "MINIO_ENDPOINT", "http://localhost:9000")
        mp.setattr(settings, "MOCK_SERVICES", False)
        assert resolve_storage_backend() == "local"
        client = StorageClient()
        assert client.use_s3 is False
