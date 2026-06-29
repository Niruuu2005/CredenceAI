import pytest
from app.services.url_canonicalizer import URLCanonicalizer
from app.services.deduplicator import DeduplicationService


def test_url_canonicalizer():
    # Strip tracking params
    url1 = "https://example.com/page?utm_source=twitter&utm_medium=social&ref=123&q=search"
    assert URLCanonicalizer.canonicalize(url1) == "https://example.com/page?q=search"

    # Default ports and trailing slashes
    url2 = "HTTPS://WWW.EXAMPLE.COM:443/path/"
    assert URLCanonicalizer.canonicalize(url2) == "https://www.example.com/path"

    # No change for standard queries
    url3 = "https://example.com/search?category=news&page=2"
    assert URLCanonicalizer.canonicalize(url3) == "https://example.com/search?category=news&page=2"


def test_deduplication_exact_url():
    service = DeduplicationService()
    
    # Items with the same canonical URL but different tracking params
    item1 = {
        "id": "res_1",
        "title": "First Result",
        "snippet": "Interesting text description of first result.",
        "url": "https://example.com/article?utm_source=news",
        "quality_scores": {"final_trust_score": 0.85}
    }
    item2 = {
        "id": "res_2",
        "title": "First Result Dup",
        "snippet": "Interesting text description of first result.",
        "url": "https://example.com/article?ref=blog",
        "quality_scores": {"final_trust_score": 0.70}  # lower score, will become duplicate
    }
    
    unique, groups = service.group_duplicates([item1, item2])
    
    assert len(unique) == 1
    assert unique[0]["id"] == "res_1"
    assert len(groups) == 1
    assert groups[0]["canonical_result_id"] == "res_1"
    assert len(groups[0]["members"]) == 1
    assert groups[0]["members"][0]["result_id"] == "res_2"
    assert groups[0]["members"][0]["match_type"] == "exact_url"


def test_deduplication_near_duplicate():
    service = DeduplicationService(jaccard_threshold=0.70)
    
    # Near duplicate titles and snippets (highly overlapping content)
    item1 = {
        "id": "res_1",
        "title": "Tesla recall update for safety issue",
        "snippet": "Tesla is recalling vehicles due to a minor safety issue with the autopilot system.",
        "url": "https://reuters.com/tesla-recall",
        "quality_scores": {"final_trust_score": 0.90}
    }
    item2 = {
        "id": "res_2",
        "title": "Tesla recalls autopilot safety issue update",
        "snippet": "Tesla recalls vehicles due to a safety issue with autopilot systems.",
        "url": "https://bloomberg.com/tesla-autopilot-recall",
        "quality_scores": {"final_trust_score": 0.80}
    }
    item3 = {
        "id": "res_3",
        "title": "Different topic altogether",
        "snippet": "This is about baking cookies and apple pies in a kitchen.",
        "url": "https://cooking.com/recipes",
        "quality_scores": {"final_trust_score": 0.60}
    }
    
    unique, groups = service.group_duplicates([item1, item2, item3])
    
    assert len(unique) == 2
    assert any(x["id"] == "res_1" for x in unique)
    assert any(x["id"] == "res_3" for x in unique)
    assert len(groups) == 1
    assert groups[0]["canonical_result_id"] == "res_1"
    assert groups[0]["members"][0]["result_id"] == "res_2"
    assert groups[0]["members"][0]["match_type"] == "near_duplicate"
