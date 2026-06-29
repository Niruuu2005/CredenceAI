"""
Unit tests for FreshnessScorer (Sprint 53)

Tests cover:
- Fresh content within TTL window
- Stale content beyond TTL
- Content change detection via hash comparison
- Domain-specific TTL overrides
- Proactive refresh recommendation at 80% TTL
- should_recrawl() helper
- Never-crawled case
- hash_html utility
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.services.freshness_scorer import FreshnessScorer


SAMPLE_TEXT = "This is sample article content about technology trends in 2024."
DIFFERENT_TEXT = "Entirely different content about cooking recipes and kitchen tips."


@pytest.fixture
def scorer():
    return FreshnessScorer()


def make_dt(seconds_ago: int) -> datetime:
    """Create a timezone-aware datetime N seconds in the past."""
    return datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)


# ──────────────────────────────────────────────
# Never-crawled case
# ──────────────────────────────────────────────

def test_never_crawled_is_stale(scorer):
    """A URL that has never been crawled should always be marked stale."""
    result = scorer.score("https://example.com/page", SAMPLE_TEXT, None, None)
    assert result["fresh"] is False
    assert result["score"] == 0.0
    assert result["recommend_recrawl"] is True


def test_never_crawled_staleness_is_negative_one(scorer):
    result = scorer.score("https://example.com/page", SAMPLE_TEXT, None, None)
    assert result["staleness_seconds"] == -1


# ──────────────────────────────────────────────
# Fresh content (within TTL)
# ──────────────────────────────────────────────

def test_fresh_within_ttl(scorer):
    """Content crawled 1 hour ago with 24h TTL should be fresh."""
    stored_hash = scorer._hash(SAMPLE_TEXT)
    last_crawled = make_dt(3600)  # 1 hour ago
    result = scorer.score("https://example.com/page", SAMPLE_TEXT, stored_hash, last_crawled)
    assert result["fresh"] is True
    assert result["score"] > 0.5
    assert result["content_changed"] is False


def test_score_near_one_when_just_crawled(scorer):
    """Score should be close to 1.0 for very recently crawled content."""
    stored_hash = scorer._hash(SAMPLE_TEXT)
    last_crawled = make_dt(10)  # 10 seconds ago
    result = scorer.score("https://example.com", SAMPLE_TEXT, stored_hash, last_crawled)
    assert result["score"] > 0.99


# ──────────────────────────────────────────────
# Stale content (beyond TTL)
# ──────────────────────────────────────────────

def test_stale_beyond_ttl(scorer):
    """Content crawled 2 days ago with 24h TTL should be stale."""
    stored_hash = scorer._hash(SAMPLE_TEXT)
    last_crawled = make_dt(172800)  # 48 hours ago
    result = scorer.score("https://example.com/old-page", SAMPLE_TEXT, stored_hash, last_crawled)
    assert result["fresh"] is False
    assert result["score"] == 0.0
    assert result["recommend_recrawl"] is True


def test_score_zero_when_beyond_ttl(scorer):
    stored_hash = scorer._hash(SAMPLE_TEXT)
    last_crawled = make_dt(200000)  # way beyond 24h TTL
    result = scorer.score("https://example.com", SAMPLE_TEXT, stored_hash, last_crawled)
    assert result["score"] == 0.0


# ──────────────────────────────────────────────
# Content change detection
# ──────────────────────────────────────────────

def test_content_changed_forces_stale(scorer):
    """Even if within TTL, content hash mismatch marks as stale."""
    old_hash = scorer._hash("Old content that has since been updated by the webmaster.")
    last_crawled = make_dt(60)  # 1 minute ago - still fresh by time
    result = scorer.score("https://example.com/page", SAMPLE_TEXT, old_hash, last_crawled)
    assert result["content_changed"] is True
    assert result["fresh"] is False
    assert result["score"] == 0.0
    assert result["recommend_recrawl"] is True


def test_same_hash_not_changed(scorer):
    """Identical content hash should not be flagged as changed."""
    stored_hash = scorer._hash(SAMPLE_TEXT)
    last_crawled = make_dt(60)
    result = scorer.score("https://example.com/page", SAMPLE_TEXT, stored_hash, last_crawled)
    assert result["content_changed"] is False


def test_none_stored_hash_not_changed(scorer):
    """When stored_hash is None, content_changed should be False (first crawl)."""
    last_crawled = make_dt(60)
    result = scorer.score("https://example.com/page", SAMPLE_TEXT, None, last_crawled)
    # None stored hash means no comparison
    assert result["content_changed"] is False


# ──────────────────────────────────────────────
# Domain-specific TTL
# ──────────────────────────────────────────────

def test_wikipedia_ttl_is_weekly(scorer):
    ttl = scorer.get_domain_ttl("https://en.wikipedia.org/wiki/Python")
    assert ttl == 604800  # 7 days


def test_news_site_ttl_is_short(scorer):
    ttl = scorer.get_domain_ttl("https://www.bbc.com/news/article")
    assert ttl == 1800  # 30 min


def test_default_ttl_24h(scorer):
    ttl = scorer.get_domain_ttl("https://unknown-site.com/page")
    assert ttl == 86400


def test_wikipedia_fresh_within_week(scorer):
    """Wikipedia content crawled 2 days ago should still be fresh."""
    stored_hash = scorer._hash(SAMPLE_TEXT)
    last_crawled = make_dt(172800)  # 48h ago
    result = scorer.score("https://en.wikipedia.org/wiki/Test", SAMPLE_TEXT, stored_hash, last_crawled)
    assert result["fresh"] is True
    assert result["ttl_seconds"] == 604800


# ──────────────────────────────────────────────
# Proactive refresh recommendation
# ──────────────────────────────────────────────

def test_proactive_refresh_at_80_percent_ttl(scorer):
    """At 80%+ of TTL expiry, recommend_recrawl should be True even if fresh."""
    stored_hash = scorer._hash(SAMPLE_TEXT)
    # 86400 * 0.85 = 73440 seconds ~ 20.4 hours ago
    last_crawled = make_dt(73440)
    result = scorer.score("https://example.com/page", SAMPLE_TEXT, stored_hash, last_crawled)
    assert result["recommend_recrawl"] is True


def test_no_proactive_refresh_when_very_fresh(scorer):
    """Very recent crawl should not trigger proactive refresh."""
    stored_hash = scorer._hash(SAMPLE_TEXT)
    last_crawled = make_dt(100)  # 100s ago, well within 80%
    result = scorer.score("https://example.com/page", SAMPLE_TEXT, stored_hash, last_crawled)
    assert result["recommend_recrawl"] is False


# ──────────────────────────────────────────────
# should_recrawl() helper
# ──────────────────────────────────────────────

def test_should_recrawl_fresh_returns_false(scorer):
    stored_hash = scorer._hash(SAMPLE_TEXT)
    last_crawled = make_dt(100)
    should, reason = scorer.should_recrawl("https://example.com", SAMPLE_TEXT, stored_hash, last_crawled)
    assert should is False
    assert reason == "fresh"


def test_should_recrawl_stale_returns_true(scorer):
    stored_hash = scorer._hash(SAMPLE_TEXT)
    last_crawled = make_dt(172800)  # 48h
    should, reason = scorer.should_recrawl("https://example.com", SAMPLE_TEXT, stored_hash, last_crawled)
    assert should is True
    assert "stale" in reason


def test_should_recrawl_content_changed(scorer):
    old_hash = scorer._hash("Old content version from yesterday")
    last_crawled = make_dt(30)
    should, reason = scorer.should_recrawl("https://example.com", SAMPLE_TEXT, old_hash, last_crawled)
    assert should is True
    assert reason == "content_changed"


def test_should_recrawl_never_crawled(scorer):
    should, reason = scorer.should_recrawl("https://example.com", SAMPLE_TEXT, None, None)
    assert should is True


# ──────────────────────────────────────────────
# hash_html utility
# ──────────────────────────────────────────────

def test_hash_html_strips_tags(scorer):
    """hash_html should produce same hash regardless of HTML tag wrapping."""
    html1 = "<html><body><p>Hello world</p></body></html>"
    html2 = "<div class='x'><span>Hello world</span></div>"
    h1 = scorer.hash_html(html1)
    h2 = scorer.hash_html(html2)
    assert h1 == h2


def test_hash_html_is_64_chars(scorer):
    h = scorer.hash_html("<html><body>Content</body></html>")
    assert len(h) == 64


def test_hash_result_in_score_output(scorer):
    """current_hash in score result should match direct _hash() call."""
    stored_hash = scorer._hash(SAMPLE_TEXT)
    last_crawled = make_dt(60)
    result = scorer.score("https://example.com", SAMPLE_TEXT, stored_hash, last_crawled)
    assert result["current_hash"] == scorer._hash(SAMPLE_TEXT)
