import pytest
from app.services.evidence_graph import Claim, EvidenceGraph
from app.services.intelligence_card import IntelligenceCard, IntelligenceCardGenerator

def test_intelligence_card_to_dict():
    """Test the to_dict method of IntelligenceCard."""
    card = IntelligenceCard(
        entity_name="OpenAI",
        entity_type="organization",
        canonical_name="OpenAI Inc.",
        wikidata_qid="Q21708200",
        description="An AI research and deployment company.",
        key_facts=[{"claim": "Fact 1", "confidence": 0.8, "corroboration": 2}],
        contradictions=[{"claim": "Contradictory Fact", "sources": ["src1"]}],
        related_entities=["Microsoft", "ChatGPT"],
        source_count=3,
        avg_confidence=0.75,
        highest_corroboration=3,
        sources=["url1", "url2", "url3"],
        vertical="company"
    )
    
    data = card.to_dict()
    assert data["entity_name"] == "OpenAI"
    assert data["entity_type"] == "organization"
    assert data["canonical_name"] == "OpenAI Inc."
    assert data["wikidata_qid"] == "Q21708200"
    assert data["description"] == "An AI research and deployment company."
    assert len(data["key_facts"]) == 1
    assert data["key_facts"][0]["claim"] == "Fact 1"
    assert data["freshness_label"] == "fresh"

def test_intelligence_card_generator_generate():
    """Test generating a card from raw data lists."""
    generator = IntelligenceCardGenerator()
    
    meta = {
        "type": "organization",
        "canonical": "CredenceAI Corp",
        "wikidata_qid": "Q12345",
        "description": "An AI safety and data verification platform."
    }
    
    evidence_nodes = [
        {"canonical_text": "Fact A", "confidence": 0.5, "corroboration_count": 1, "supporting_sources": ["url1"]},
        {"canonical_text": "Fact B", "confidence": 0.9, "corroboration_count": 3, "supporting_sources": ["url2", "url3"]}
    ]
    
    contradictions = [{"claim": "Fact A is false", "sources": ["url4"]}]
    sources = ["url1", "url2", "url3", "url4"]
    
    card = generator.generate(
        entity_name="CredenceAI",
        entity_meta=meta,
        evidence_nodes=evidence_nodes,
        contradictions=contradictions,
        sources=sources,
        vertical="research"
    )
    
    assert card.entity_name == "CredenceAI"
    assert card.entity_type == "organization"
    assert card.wikidata_qid == "Q12345"
    assert card.avg_confidence == 0.7  # (0.5 + 0.9) / 2
    assert card.highest_corroboration == 3
    assert len(card.key_facts) == 2
    # Check that they are sorted by confidence descending (Fact B has 0.9, Fact A has 0.5)
    assert card.key_facts[0]["claim"] == "Fact B"
    assert card.key_facts[1]["claim"] == "Fact A"
    
    # Check cache retrieval methods
    assert generator.get_card("CredenceAI") == card
    assert generator.get_card("credenceai") == card  # case insensitive
    assert "credenceai" in generator.list_cards()
    
    exported = generator.export_all()
    assert len(exported) == 1
    assert exported[0]["entity_name"] == "CredenceAI"

def test_intelligence_card_generator_from_graph():
    """Test generating a card directly from an EvidenceGraph instance."""
    graph = EvidenceGraph()
    
    # Setup some claims for the graph
    c1 = Claim(
        claim_id="c1",
        text="Python 3.13 was released in 2024",
        entity="Python",
        source_url="https://python.org",
        source_reliability=0.9
    )
    c2 = Claim(
        claim_id="c2",
        text="Python is used for data science",
        entity="Python",
        source_url="https://wikipedia.org",
        source_reliability=0.8
    )
    c3 = Claim(
        claim_id="c3",
        text="Python 3.13 was released in 2025",
        entity="Python",
        source_url="https://unreliableblog.com",
        source_reliability=0.4
    )
    
    graph.add_claim(c1)
    graph.add_claim(c2)
    graph.add_claim(c3)
    
    # Add contradiction
    graph.add_contradiction("Python 3.13 was released in 2024", "Python 3.13 was released in 2025", source_url="https://news.com")
    
    generator = IntelligenceCardGenerator()
    meta = {
        "type": "technology",
        "description": "A popular programming language."
    }
    
    card = generator.generate_from_graph(
        entity_name="Python",
        entity_meta=meta,
        evidence_graph=graph,
        vertical="technology"
    )
    
    assert card.entity_name == "Python"
    assert card.entity_type == "technology"
    assert len(card.key_facts) >= 3
    # Check that contradictions are extracted
    assert len(card.contradictions) > 0
    # Check sources
    assert "https://python.org" in card.sources
    assert "https://wikipedia.org" in card.sources
