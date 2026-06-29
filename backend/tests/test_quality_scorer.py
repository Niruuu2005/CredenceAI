import pytest
import datetime
from app.services.source_registry import SourceReliabilityRegistry
from app.services.quality_scorer import QualityScorer


def test_source_reliability():
    registry = SourceReliabilityRegistry()
    
    # Direct match trusted
    assert registry.get_reliability_score("https://openalex.org/works") == 0.95
    assert registry.get_reliability_score("https://en.wikipedia.org/wiki/Tesla") == 0.90
    assert registry.get_reliability_score("https://reuters.com/news") == 0.88
    
    # Government / Educational suffixes
    assert registry.get_reliability_score("https://www.nasa.gov/article") == 0.90
    assert registry.get_reliability_score("https://stanford.edu/class") == 0.90
    
    # Untrusted / Social
    assert registry.get_reliability_score("https://x.com/post") == 0.40
    assert registry.get_reliability_score("https://reddit.com/r/learnprogramming") == 0.40
    
    # Fallback
    assert registry.get_reliability_score("https://randomblog.com/post", "searxng") == 0.70
    assert registry.get_reliability_score("https://randomblog.com/post", "unknown") == 0.60


def test_relevance_scorer():
    scorer = QualityScorer()
    query = "artificial intelligence machine learning"
    
    # Full match
    title = "Artificial Intelligence and Machine Learning guide"
    snippet = "Learn how artificial intelligence and machine learning work."
    assert scorer.calculate_relevance_score(query, title, snippet) == 1.0
    
    # Partial match (2 out of 4 words: "intelligence", "learning")
    title2 = "Intelligence reports on human learning"
    snippet2 = "This report discusses human learning patterns."
    assert scorer.calculate_relevance_score(query, title2, snippet2) == 0.5
    
    # No match
    assert scorer.calculate_relevance_score(query, "cooking recipes", "how to bake cake") == 0.0


def test_freshness_scorer():
    scorer = QualityScorer()
    now = datetime.datetime.now(datetime.UTC)
    
    # Today
    assert scorer.calculate_freshness_score(now) == 1.0
    
    # 1 year ago (halved)
    one_year_ago = now - datetime.timedelta(days=365)
    assert scorer.calculate_freshness_score(one_year_ago) == 0.50
    
    # 2 years ago (quartered)
    two_years_ago = now - datetime.timedelta(days=730)
    assert scorer.calculate_freshness_score(two_years_ago) == 0.25
    
    # None fallback
    assert scorer.calculate_freshness_score(None) == 0.5


def test_authority_scorer():
    scorer = QualityScorer()
    
    # High authoritygov
    assert scorer.calculate_authority_score("https://nasa.gov") == 0.95
    # High authority gov with depth penalty
    assert scorer.calculate_authority_score("https://nasa.gov/science/mars/rover") == 0.86
    
    # Org extension
    assert scorer.calculate_authority_score("https://w3c.org") == 0.80
    
    # Standard com extension
    assert scorer.calculate_authority_score("https://example.com") == 0.65


def test_score_result():
    scorer = QualityScorer()
    query = "artificial intelligence machine learning"
    
    # High-quality article (Accept)
    item_high = {
        "title": "Artificial Intelligence and Machine Learning Developments",
        "snippet": "We cover recent advances in artificial intelligence and machine learning algorithms.",
        "url": "https://nature.com/articles/ai-ml-2026",
        "source": "openalex",
        "published_at": datetime.datetime.now(datetime.UTC)
    }
    scores_high = scorer.score_result(query, item_high)
    assert scores_high["final_trust_score"] >= 0.70
    assert scores_high["decision"] == "accept"
    
    # Medium-quality article (Review)
    item_med = {
        "title": "Learning about intelligence",
        "snippet": "Simple ways to understand computer intelligence.",
        "url": "https://randomblog.com/post",
        "source": "searxng",
        "published_at": datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=365)
    }
    scores_med = scorer.score_result(query, item_med)
    assert 0.40 <= scores_med["final_trust_score"] < 0.70
    assert scores_med["decision"] == "review"
    
    # Low-quality spam link (Reject)
    item_low = {
        "title": "baking cake recipes",
        "snippet": "learn how to cook food easily.",
        "url": "https://spamsite.xyz/forum/thread",
        "source": "searxng",
        "published_at": datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=2000)
    }
    scores_low = scorer.score_result(query, item_low)
    assert scores_low["final_trust_score"] < 0.40
    assert scores_low["decision"] == "reject"
