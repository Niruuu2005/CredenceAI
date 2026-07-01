"""Tests for production startup validation."""

import pytest
from app.config import settings
from app import startup_validation


def test_production_requires_jwt_secret():
    original = settings.APP_ENV, settings.JWT_SECRET
    settings.APP_ENV = "production"
    settings.JWT_SECRET = "change-me"
    try:
        with pytest.raises(RuntimeError, match="JWT_SECRET"):
            startup_validation.validate_production_config()
    finally:
        settings.APP_ENV, settings.JWT_SECRET = original


def test_production_requires_at_least_one_oauth_provider():
    original = (
        settings.APP_ENV,
        settings.JWT_SECRET,
        settings.GOOGLE_CLIENT_ID,
        settings.GOOGLE_CLIENT_SECRET,
        settings.GOOGLE_REDIRECT_URI,
        settings.GITHUB_CLIENT_ID,
        settings.GITHUB_CLIENT_SECRET,
        settings.GITHUB_REDIRECT_URI,
    )
    settings.APP_ENV = "production"
    settings.JWT_SECRET = "a" * 64
    settings.GOOGLE_CLIENT_ID = None
    settings.GOOGLE_CLIENT_SECRET = None
    settings.GOOGLE_REDIRECT_URI = None
    settings.GITHUB_CLIENT_ID = None
    settings.GITHUB_CLIENT_SECRET = None
    settings.GITHUB_REDIRECT_URI = None
    try:
        with pytest.raises(RuntimeError, match="OAuth provider"):
            startup_validation.validate_production_config()
    finally:
        (
            settings.APP_ENV,
            settings.JWT_SECRET,
            settings.GOOGLE_CLIENT_ID,
            settings.GOOGLE_CLIENT_SECRET,
            settings.GOOGLE_REDIRECT_URI,
            settings.GITHUB_CLIENT_ID,
            settings.GITHUB_CLIENT_SECRET,
            settings.GITHUB_REDIRECT_URI,
        ) = original


def test_production_passes_with_github_only():
    original = (
        settings.APP_ENV,
        settings.JWT_SECRET,
        settings.GOOGLE_CLIENT_ID,
        settings.GOOGLE_CLIENT_SECRET,
        settings.GOOGLE_REDIRECT_URI,
        settings.GITHUB_CLIENT_ID,
        settings.GITHUB_CLIENT_SECRET,
        settings.GITHUB_REDIRECT_URI,
        settings.CORS_ALLOWED_ORIGINS,
        settings.SEARXNG_BASE_URL,
        settings.MOCK_SERVICES,
        settings.SEARCH_PROVIDER,
        settings.CELERY_ALWAYS_EAGER,
    )
    settings.APP_ENV = "production"
    settings.JWT_SECRET = "a" * 64
    settings.GOOGLE_CLIENT_ID = None
    settings.GOOGLE_CLIENT_SECRET = None
    settings.GOOGLE_REDIRECT_URI = None
    settings.GITHUB_CLIENT_ID = "gh_client"
    settings.GITHUB_CLIENT_SECRET = "gh_secret"
    settings.GITHUB_REDIRECT_URI = "https://app.example.com/auth/github/callback"
    settings.CORS_ALLOWED_ORIGINS = ["https://app.example.com"]
    settings.SEARXNG_BASE_URL = "https://searxng.example.com"
    settings.MOCK_SERVICES = False
    settings.SEARCH_PROVIDER = "duckduckgo"
    settings.CELERY_ALWAYS_EAGER = False
    try:
        startup_validation.validate_production_config()
    finally:
        (
            settings.APP_ENV,
            settings.JWT_SECRET,
            settings.GOOGLE_CLIENT_ID,
            settings.GOOGLE_CLIENT_SECRET,
            settings.GOOGLE_REDIRECT_URI,
            settings.GITHUB_CLIENT_ID,
            settings.GITHUB_CLIENT_SECRET,
            settings.GITHUB_REDIRECT_URI,
            settings.CORS_ALLOWED_ORIGINS,
            settings.SEARXNG_BASE_URL,
            settings.MOCK_SERVICES,
            settings.SEARCH_PROVIDER,
            settings.CELERY_ALWAYS_EAGER,
        ) = original


def test_production_rejects_localhost_only_cors():
    original = (
        settings.APP_ENV,
        settings.JWT_SECRET,
        settings.GOOGLE_CLIENT_ID,
        settings.GOOGLE_CLIENT_SECRET,
        settings.GOOGLE_REDIRECT_URI,
        settings.GITHUB_CLIENT_ID,
        settings.GITHUB_CLIENT_SECRET,
        settings.GITHUB_REDIRECT_URI,
        settings.CORS_ALLOWED_ORIGINS,
    )
    settings.APP_ENV = "production"
    settings.JWT_SECRET = "a" * 64
    settings.GOOGLE_CLIENT_ID = None
    settings.GOOGLE_CLIENT_SECRET = None
    settings.GOOGLE_REDIRECT_URI = None
    settings.GITHUB_CLIENT_ID = "gh_client"
    settings.GITHUB_CLIENT_SECRET = "gh_secret"
    settings.GITHUB_REDIRECT_URI = "https://app.example.com/auth/github/callback"
    settings.CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
    try:
        with pytest.raises(RuntimeError, match="CORS_ALLOWED_ORIGINS"):
            startup_validation.validate_production_config()
    finally:
        (
            settings.APP_ENV,
            settings.JWT_SECRET,
            settings.GOOGLE_CLIENT_ID,
            settings.GOOGLE_CLIENT_SECRET,
            settings.GOOGLE_REDIRECT_URI,
            settings.GITHUB_CLIENT_ID,
            settings.GITHUB_CLIENT_SECRET,
            settings.GITHUB_REDIRECT_URI,
            settings.CORS_ALLOWED_ORIGINS,
        ) = original


def test_production_rejects_localhost_searxng_when_provider_searxng():
    original = (
        settings.APP_ENV,
        settings.JWT_SECRET,
        settings.GOOGLE_CLIENT_ID,
        settings.GOOGLE_CLIENT_SECRET,
        settings.GOOGLE_REDIRECT_URI,
        settings.GITHUB_CLIENT_ID,
        settings.GITHUB_CLIENT_SECRET,
        settings.GITHUB_REDIRECT_URI,
        settings.CORS_ALLOWED_ORIGINS,
        settings.SEARXNG_BASE_URL,
        settings.MOCK_SERVICES,
        settings.SEARCH_PROVIDER,
    )
    settings.APP_ENV = "production"
    settings.JWT_SECRET = "a" * 64
    settings.GOOGLE_CLIENT_ID = None
    settings.GOOGLE_CLIENT_SECRET = None
    settings.GOOGLE_REDIRECT_URI = None
    settings.GITHUB_CLIENT_ID = "gh_client"
    settings.GITHUB_CLIENT_SECRET = "gh_secret"
    settings.GITHUB_REDIRECT_URI = "https://app.example.com/auth/github/callback"
    settings.CORS_ALLOWED_ORIGINS = ["https://app.example.com"]
    settings.SEARXNG_BASE_URL = "http://localhost:8080"
    settings.MOCK_SERVICES = False
    settings.SEARCH_PROVIDER = "searxng"
    try:
        with pytest.raises(RuntimeError, match="SEARXNG_BASE_URL"):
            startup_validation.validate_production_config()
    finally:
        (
            settings.APP_ENV,
            settings.JWT_SECRET,
            settings.GOOGLE_CLIENT_ID,
            settings.GOOGLE_CLIENT_SECRET,
            settings.GOOGLE_REDIRECT_URI,
            settings.GITHUB_CLIENT_ID,
            settings.GITHUB_CLIENT_SECRET,
            settings.GITHUB_REDIRECT_URI,
            settings.CORS_ALLOWED_ORIGINS,
            settings.SEARXNG_BASE_URL,
            settings.MOCK_SERVICES,
            settings.SEARCH_PROVIDER,
        ) = original


def test_production_passes_with_duckduckgo_and_localhost_searxng():
    original = (
        settings.APP_ENV,
        settings.JWT_SECRET,
        settings.GOOGLE_CLIENT_ID,
        settings.GOOGLE_CLIENT_SECRET,
        settings.GOOGLE_REDIRECT_URI,
        settings.GITHUB_CLIENT_ID,
        settings.GITHUB_CLIENT_SECRET,
        settings.GITHUB_REDIRECT_URI,
        settings.CORS_ALLOWED_ORIGINS,
        settings.SEARXNG_BASE_URL,
        settings.MOCK_SERVICES,
        settings.SEARCH_PROVIDER,
        settings.CELERY_ALWAYS_EAGER,
    )
    settings.APP_ENV = "production"
    settings.JWT_SECRET = "a" * 64
    settings.GOOGLE_CLIENT_ID = None
    settings.GOOGLE_CLIENT_SECRET = None
    settings.GOOGLE_REDIRECT_URI = None
    settings.GITHUB_CLIENT_ID = "gh_client"
    settings.GITHUB_CLIENT_SECRET = "gh_secret"
    settings.GITHUB_REDIRECT_URI = "https://app.example.com/auth/github/callback"
    settings.CORS_ALLOWED_ORIGINS = ["https://app.example.com"]
    settings.SEARXNG_BASE_URL = "http://localhost:8080"
    settings.MOCK_SERVICES = False
    settings.SEARCH_PROVIDER = "duckduckgo"
    settings.CELERY_ALWAYS_EAGER = False
    try:
        startup_validation.validate_production_config()
    finally:
        (
            settings.APP_ENV,
            settings.JWT_SECRET,
            settings.GOOGLE_CLIENT_ID,
            settings.GOOGLE_CLIENT_SECRET,
            settings.GOOGLE_REDIRECT_URI,
            settings.GITHUB_CLIENT_ID,
            settings.GITHUB_CLIENT_SECRET,
            settings.GITHUB_REDIRECT_URI,
            settings.CORS_ALLOWED_ORIGINS,
            settings.SEARXNG_BASE_URL,
            settings.MOCK_SERVICES,
            settings.SEARCH_PROVIDER,
            settings.CELERY_ALWAYS_EAGER,
        ) = original


def test_production_rejects_celery_always_eager():
    original = (
        settings.APP_ENV,
        settings.JWT_SECRET,
        settings.GOOGLE_CLIENT_ID,
        settings.GOOGLE_CLIENT_SECRET,
        settings.GOOGLE_REDIRECT_URI,
        settings.GITHUB_CLIENT_ID,
        settings.GITHUB_CLIENT_SECRET,
        settings.GITHUB_REDIRECT_URI,
        settings.CORS_ALLOWED_ORIGINS,
        settings.CELERY_ALWAYS_EAGER,
    )
    settings.APP_ENV = "production"
    settings.JWT_SECRET = "a" * 64
    settings.GOOGLE_CLIENT_ID = None
    settings.GOOGLE_CLIENT_SECRET = None
    settings.GOOGLE_REDIRECT_URI = None
    settings.GITHUB_CLIENT_ID = "gh_client"
    settings.GITHUB_CLIENT_SECRET = "gh_secret"
    settings.GITHUB_REDIRECT_URI = "https://app.example.com/auth/github/callback"
    settings.CORS_ALLOWED_ORIGINS = ["https://app.example.com"]
    settings.CELERY_ALWAYS_EAGER = True
    try:
        with pytest.raises(RuntimeError, match="CELERY_ALWAYS_EAGER"):
            startup_validation.validate_production_config()
    finally:
        (
            settings.APP_ENV,
            settings.JWT_SECRET,
            settings.GOOGLE_CLIENT_ID,
            settings.GOOGLE_CLIENT_SECRET,
            settings.GOOGLE_REDIRECT_URI,
            settings.GITHUB_CLIENT_ID,
            settings.GITHUB_CLIENT_SECRET,
            settings.GITHUB_REDIRECT_URI,
            settings.CORS_ALLOWED_ORIGINS,
            settings.CELERY_ALWAYS_EAGER,
        ) = original
