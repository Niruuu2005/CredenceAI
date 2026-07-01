"""Tests for Redis/Celery SSL configuration helpers."""
import ssl

from app.utils.redis_ssl import (
    celery_ssl_options,
    ensure_rediss_ssl_query_param,
    is_rediss_url,
    redis_client_kwargs,
    resolve_ssl_cert_reqs,
)


def test_is_rediss_url():
    assert is_rediss_url("rediss://host:6379/0")
    assert not is_rediss_url("redis://host:6379/0")


def test_resolve_ssl_cert_reqs_from_url():
    url = "rediss://default:pass@host:6379/0?ssl_cert_reqs=CERT_NONE"
    assert resolve_ssl_cert_reqs(url) == ssl.CERT_NONE


def test_resolve_ssl_cert_reqs_default():
    url = "rediss://default:pass@host:6379/0"
    assert resolve_ssl_cert_reqs(url, "CERT_REQUIRED") == ssl.CERT_REQUIRED


def test_celery_ssl_options():
    opts = celery_ssl_options("rediss://host/0", "CERT_OPTIONAL")
    assert opts["ssl_cert_reqs"] == ssl.CERT_OPTIONAL


def test_redis_client_kwargs_for_plain_redis():
    assert redis_client_kwargs("redis://localhost:6379/0") == {}


def test_redis_client_kwargs_for_rediss():
    kwargs = redis_client_kwargs("rediss://host/0", "CERT_REQUIRED")
    assert kwargs["ssl"] is True
    assert kwargs["ssl_cert_reqs"] == ssl.CERT_REQUIRED


def test_ensure_rediss_ssl_query_param_appends_when_missing():
    url = "rediss://default:pass@host:6379/0"
    normalized = ensure_rediss_ssl_query_param(url, "CERT_REQUIRED")
    assert "ssl_cert_reqs=CERT_REQUIRED" in normalized
    assert normalized.startswith("rediss://")


def test_ensure_rediss_ssl_query_param_preserves_existing():
    url = "rediss://default:pass@host:6379/0?ssl_cert_reqs=CERT_NONE"
    assert ensure_rediss_ssl_query_param(url) == url


def test_ensure_rediss_ssl_query_param_plain_redis_unchanged():
    url = "redis://localhost:6379/0"
    assert ensure_rediss_ssl_query_param(url) == url


def test_settings_redis_url_normalizes_rediss():
    from app.config import Settings

    s = Settings(
        REDIS_URL="rediss://default:secret@upstash.example:6379/0",
        REDIS_SSL_CERT_REQS="CERT_REQUIRED",
    )
    assert "ssl_cert_reqs=CERT_REQUIRED" in s.redis_url
    assert "ssl_cert_reqs=CERT_REQUIRED" in s.celery_broker_url
