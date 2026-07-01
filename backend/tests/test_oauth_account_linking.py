"""Tests for cross-provider OAuth account linking."""

from app.api.auth import _issue_session_for_user
from app.models import User


def test_oauth_reuses_existing_user_by_email(db_session):
    existing = User(id="gh_user_1", email="same@example.com", name="GitHub Name")
    db_session.add(existing)
    db_session.commit()

    result = _issue_session_for_user(
        db_session,
        user_id="google_sub_999",
        email="same@example.com",
        name="Google Name",
        picture="https://example.com/pic.jpg",
    )

    assert result["user"]["id"] == "gh_user_1"
    assert result["user"]["email"] == "same@example.com"
    assert result["user"]["name"] == "Google Name"
    assert result["user"]["picture"] == "https://example.com/pic.jpg"
    assert db_session.query(User).filter(User.email == "same@example.com").count() == 1
