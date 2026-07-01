"""Tests for Render self keep-alive URL resolution."""

import os

from app.config import settings
from app.services import self_keepalive


def test_resolve_health_url_from_render_external_url(monkeypatch):
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://credenceai-api.onrender.com")
    monkeypatch.setattr(settings, "API_PUBLIC_URL", None)
    assert (
        self_keepalive.resolve_self_keepalive_health_url()
        == "https://credenceai-api.onrender.com/api/health"
    )


def test_resolve_health_url_from_api_public_url(monkeypatch):
    monkeypatch.delenv("RENDER_EXTERNAL_URL", raising=False)
    monkeypatch.setattr(settings, "API_PUBLIC_URL", "https://api.example.com/")
    assert (
        self_keepalive.resolve_self_keepalive_health_url()
        == "https://api.example.com/api/health"
    )


def test_resolve_health_url_missing_returns_none(monkeypatch):
    monkeypatch.delenv("RENDER_EXTERNAL_URL", raising=False)
    monkeypatch.setattr(settings, "API_PUBLIC_URL", None)
    assert self_keepalive.resolve_self_keepalive_health_url() is None
