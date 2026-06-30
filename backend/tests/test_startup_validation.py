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
    )
    settings.APP_ENV = "production"
    settings.JWT_SECRET = "a" * 64
    settings.GOOGLE_CLIENT_ID = None
    settings.GOOGLE_CLIENT_SECRET = None
    settings.GOOGLE_REDIRECT_URI = None
    settings.GITHUB_CLIENT_ID = "gh_client"
    settings.GITHUB_CLIENT_SECRET = "gh_secret"
    settings.GITHUB_REDIRECT_URI = "https://app.example.com/auth/github/callback"
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
        ) = original
