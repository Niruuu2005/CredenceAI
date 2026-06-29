import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.services.entity_resolver import EntityResolver
import app.services.repository as repo
from app.models import Entity, EntityLink, EntityAlias


def test_extract_candidates():
    # Setup resolver with dummy DB session
    resolver = EntityResolver(MagicMock(spec=Session))
    
    text = "Yesterday Elon Musk and Tesla Inc. announced a new safety update in San Francisco."
    candidates = resolver.extract_candidates(text)
    
    assert "Elon Musk" in candidates
    assert "Tesla Inc" in candidates or "Tesla" in candidates or any("Tesla" in c for c in candidates)
    assert "San Francisco" in candidates
    assert "Yesterday" not in candidates
    assert "Yesterday Elon Musk" not in candidates
    
    # Test ignored words list
    assert "The" not in candidates
    assert "And" not in candidates


def test_calculate_match_confidence():
    resolver = EntityResolver(MagicMock(spec=Session))
    
    # Exact match
    assert resolver.calculate_match_confidence("Tesla", "Tesla", "Electric car company", "Tesla is cool") == 0.95
    
    # Prefix/Suffix match
    assert resolver.calculate_match_confidence("Tesla", "Tesla Inc.", "Electric car company", "Tesla is cool") == 0.85
    
    # Disjoint match
    assert resolver.calculate_match_confidence("Apple", "Microsoft", "", "") == 0.0


@patch("app.services.entity_resolver.WikipediaClient")
@patch("app.services.entity_resolver.WikidataClient")
def test_resolve_and_link_entities(mock_wikidata_cls, mock_wikipedia_cls):
    # Setup mock clients
    mock_wikidata = mock_wikidata_cls.return_value
    mock_wikipedia = mock_wikipedia_cls.return_value
    
    mock_wikidata.enabled = True
    mock_wikipedia.enabled = True
    
    # Mock search_entities
    mock_wikidata.search_entities.side_effect = lambda query, limit: [
        {
            "wikidata_id": "Q11583",
            "canonical_name": "Tesla",
            "description": "American electric vehicle and clean energy company",
            "wikidata_url": "https://www.wikidata.org/wiki/Q11583",
            "entity_type": "company"
        }
    ] if "Tesla" in query else []
    
    # Mock get_entity_details
    mock_wikidata.get_entity_details.return_value = {
        "aliases": ["Tesla Motors", "Tesla Inc."],
        "description": "American electric vehicle and clean energy company"
    }
    
    # Mock Wikipedia get_page_summary
    mock_wikipedia.get_page_summary.return_value = {
        "wikipedia_url": "https://en.wikipedia.org/wiki/Tesla,_Inc."
    }
    
    # Setup database mocks
    db_session = MagicMock(spec=Session)
    resolver = EntityResolver(db_session)
    
    # Mock repository methods
    with patch("app.services.repository.get_entity_by_wikidata_id", return_value=None) as mock_get_ent, \
         patch("app.services.repository.create_entity") as mock_create_ent, \
         patch("app.services.repository.create_entity_alias") as mock_create_alias, \
         patch("app.services.repository.create_entity_link") as mock_create_link:
         
        mock_entity = MagicMock(spec=Entity)
        mock_entity.id = "ent_123"
        mock_entity.canonical_name = "Tesla"
        mock_entity.wikidata_id = "Q11583"
        mock_create_ent.return_value = mock_entity
        
        links = resolver.resolve_and_link_entities(
            result_id="res_abc",
            title="Tesla Autopilot",
            snippet="A report on electric vehicles."
        )
        
        # Verify Wikidata search was called
        mock_wikidata.search_entities.assert_called()
        
        # Verify entity creation was called since it was not in DB
        mock_create_ent.assert_called_once()
        
        # Verify alias storage
        assert mock_create_alias.call_count >= 1
        
        # Verify link storage
        mock_create_link.assert_called_once()
        
        # Verify return structure
        assert len(links) == 1
        assert links[0]["canonical_name"] == "Tesla"
        assert links[0]["wikidata_id"] == "Q11583"
        assert links[0]["confidence"] >= 0.85
