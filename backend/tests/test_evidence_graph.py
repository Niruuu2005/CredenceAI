import pytest
from app.services.evidence_graph import Claim, EvidenceGraph, ClaimNode, ClaimEdge

def test_evidence_graph_normalise():
    """Test the static _normalise method."""
    assert EvidenceGraph._normalise("  Test CLAIM! ") == "test claim"
    assert EvidenceGraph._normalise("Multiple   Spaces") == "multiple spaces"

def test_evidence_graph_add_claim_new():
    """Test adding a claim that does not exist in the graph yet."""
    graph = EvidenceGraph()
    claim = Claim(
        claim_id="c1",
        text="CredenceAI is a great tool",
        entity="CredenceAI",
        claim_type="factual",
        source_url="https://example.com/source1",
        source_reliability=0.8
    )
    
    node = graph.add_claim(claim)
    assert node is not None
    assert node.canonical_text == "CredenceAI is a great tool"
    assert node.entity == "CredenceAI"
    assert node.corroboration_count == 1
    assert node.supporting_sources == ["https://example.com/source1"]
    assert node.avg_source_reliability == 0.8
    
    # Retrieve via get_node
    retrieved = graph.get_node("CredenceAI is a great tool")
    assert retrieved == node

def test_evidence_graph_add_claim_corroborate():
    """Test that adding an equivalent claim corroborates it."""
    graph = EvidenceGraph()
    claim1 = Claim(
        claim_id="c1",
        text="CredenceAI is a great tool",
        entity="CredenceAI",
        claim_type="factual",
        source_url="https://example.com/source1",
        source_reliability=0.8
    )
    claim2 = Claim(
        claim_id="c2",
        text="  credenceai IS a great tool! ",
        entity="CredenceAI",
        claim_type="factual",
        source_url="https://example.com/source2",
        source_reliability=0.6
    )
    
    graph.add_claim(claim1)
    node = graph.add_claim(claim2)
    
    assert node.corroboration_count == 2
    assert node.supporting_sources == ["https://example.com/source1", "https://example.com/source2"]
    # Average of 0.8 and 0.6 is 0.7
    assert pytest.approx(node.avg_source_reliability) == 0.7

def test_evidence_graph_add_contradiction():
    """Test contradiction registration between claims."""
    graph = EvidenceGraph()
    claim1 = Claim(
        claim_id="c1",
        text="CredenceAI is fast",
        entity="CredenceAI",
        source_url="https://example.com/source1"
    )
    claim2 = Claim(
        claim_id="c2",
        text="CredenceAI is slow",
        entity="CredenceAI",
        source_url="https://example.com/source2"
    )
    
    graph.add_claim(claim1)
    graph.add_claim(claim2)
    
    # Register contradiction
    success = graph.add_contradiction("CredenceAI is fast", "CredenceAI is slow", source_url="https://example.com/contradict")
    assert success is True
    
    node_fast = graph.get_node("CredenceAI is fast")
    node_slow = graph.get_node("CredenceAI is slow")
    
    assert node_fast.contradiction_count == 1
    assert node_slow.contradiction_count == 1
    assert "https://example.com/contradict" in node_fast.contradicting_sources
    assert "https://example.com/contradict" in node_slow.contradicting_sources
    
    # Check edges
    assert len(graph.edges) == 1
    assert graph.edges[0].relationship == "contradicts"
    
    # Test nonexistent contradiction
    success_none = graph.add_contradiction("nonexistent", "CredenceAI is slow")
    assert success_none is False

def test_evidence_graph_support_edge():
    """Test adding a directed supports edge."""
    graph = EvidenceGraph()
    claim1 = Claim(claim_id="c1", text="CredenceAI uses AI", entity="CredenceAI")
    claim2 = Claim(claim_id="c2", text="CredenceAI is smart", entity="CredenceAI")
    graph.add_claim(claim1)
    graph.add_claim(claim2)
    
    success = graph.add_support_edge("CredenceAI uses AI", "CredenceAI is smart", weight=0.9)
    assert success is True
    assert len(graph.edges) == 1
    assert graph.edges[0].relationship == "supports"
    assert graph.edges[0].weight == 0.9
    
    success_none = graph.add_support_edge("nonexistent", "CredenceAI is smart")
    assert success_none is False

def test_evidence_graph_confidence_calculation():
    """Test confidence property calculation."""
    # confidence = reliability + boost - penalty (clamped to 0.0-1.0)
    # boost = min(1.0, corroboration_count * 0.15)
    # penalty = min(0.5, contradiction_count * 0.10)
    
    # Case 1: Simple claim
    node1 = ClaimNode(
        node_id="n1",
        canonical_text="c1",
        entity="e",
        corroboration_count=1,
        contradiction_count=0,
        avg_source_reliability=0.5
    )
    # confidence = 0.5 + min(1.0, 1 * 0.15) - 0.0 = 0.65
    assert pytest.approx(node1.confidence) == 0.65
    
    # Case 2: Highly corroborated and contradicted
    node2 = ClaimNode(
        node_id="n2",
        canonical_text="c2",
        entity="e",
        corroboration_count=4,  # boost = min(1.0, 0.60) = 0.60
        contradiction_count=2,  # penalty = min(0.5, 0.20) = 0.20
        avg_source_reliability=0.5
    )
    # confidence = 0.5 + 0.6 - 0.2 = 0.9
    assert pytest.approx(node2.confidence) == 0.9

def test_evidence_graph_get_top_claims_and_summarise():
    """Test retrieving top claims and generating summary."""
    graph = EvidenceGraph()
    # Let's add multiple claims for "CredenceAI" with different confidences
    c1 = Claim(claim_id="c1", text="C1", entity="CredenceAI", source_reliability=0.4) # confidence = 0.4 + 0.15 = 0.55
    c2 = Claim(claim_id="c2", text="C2", entity="CredenceAI", source_reliability=0.8) # confidence = 0.8 + 0.15 = 0.95
    c3 = Claim(claim_id="c3", text="C3", entity="CredenceAI", source_reliability=0.6) # confidence = 0.6 + 0.15 = 0.75
    c4 = Claim(claim_id="c4", text="Other", entity="OtherEntity", source_reliability=0.9)
    
    graph.add_claim(c1)
    graph.add_claim(c2)
    graph.add_claim(c3)
    graph.add_claim(c4)
    
    # Top claims for CredenceAI should be C2, then C3, then C1
    top = graph.get_top_claims("CredenceAI", top_n=2)
    assert len(top) == 2
    assert top[0].canonical_text == "C2"
    assert top[1].canonical_text == "C3"
    
    summary = graph.summarise()
    assert summary["total_nodes"] == 4
    assert summary["total_entities"] == 2
    
    exported = graph.export()
    assert "nodes" in exported
    assert "edges" in exported
    assert "summary" in exported
