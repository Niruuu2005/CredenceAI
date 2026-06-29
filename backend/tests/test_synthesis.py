import pytest
from app.services.synthesis import SynthesisService
from app.services.vertical_packs import CompanyPack, RAGPack

@pytest.mark.asyncio
async def test_synthesis_service_mock():
    """Test synthesis service in default mock mode."""
    service = SynthesisService()
    service.mock_mode = True

    documents = [
        {"title": "Doc A", "url": "https://a.com", "snippet": "Snippet A", "source": "searxng"},
        {"title": "Doc B", "url": "https://b.com", "snippet": "Snippet B", "source": "wikipedia"}
    ]

    out = await service.synthesize("test query", documents)
    assert out.confidence_score == 0.85
    assert len(out.citations) == 2
    assert out.citations[1].title == "Doc A"
    assert out.citations[2].url == "https://b.com"
    assert "Doc A" in out.summary
    assert "Doc B" in out.summary

def test_company_pack_profile_extraction():
    """Test extracting structured company profiles from factual nodes."""
    pack = CompanyPack()
    
    facts = [
        {"claim": "Tesla was founded by Martin Eberhard and Marc Tarpenning in 2003."},
        {"claim": "Tesla competes with Rivian and Lucid Motors in the EV space."},
        {"claim": "Tesla raised $50 million in Series A funding led by Elon Musk."}
    ]
    
    profile = pack.extract_profile("Tesla", facts)
    
    assert profile.company_name == "Tesla"
    assert "Martin Eberhard" in profile.founders
    assert "Marc Tarpenning" in profile.founders
    assert "Rivian" in profile.competitors
    assert "Lucid Motors" in profile.competitors
    assert len(profile.funding_events) == 1
    assert profile.funding_events[0]["round"] == "Series A"
    assert profile.funding_events[0]["amount"] == "$50 million"

def test_rag_pack_export():
    """Test RAGPack exports."""
    pack = RAGPack()
    
    documents = [
        {"title": "Title A", "body_text": "Text content of A"},
        {"title": "Title B", "snippet": "Snippet content of B"}
    ]
    synthesis = "This is a synthesis."
    
    json_out = pack.export_json("Query text", documents, synthesis)
    assert "Query text" in json_out
    assert "Title A" in json_out
    assert "This is a synthesis." in json_out
    
    csv_out = pack.export_csv("Query text", documents, synthesis)
    assert "instruction,context,response" in csv_out
    assert "Query text" in csv_out
    assert "Text content of A" in csv_out

def test_api_synthesis_and_export(client):
    """Test API synthesis and export endpoints."""
    # First submit a job
    payload = {
        "job_type": "search_query",
        "input": "test API synthesis"
    }
    submit_res = client.post("/jobs", json=payload)
    assert submit_res.status_code == 202
    job_id = submit_res.json()["job_id"]
    
    # Get synthesis
    syn_res = client.get(f"/jobs/{job_id}/synthesis")
    assert syn_res.status_code == 200
    data = syn_res.json()
    assert "summary" in data
    assert "citations" in data
    assert "confidence_score" in data
    
    # Export JSON
    exp_res_json = client.post(f"/jobs/{job_id}/export", json={"format": "json"})
    assert exp_res_json.status_code == 200
    assert exp_res_json.json()["format"] == "json"
    assert "test API synthesis" in exp_res_json.json()["content"]
    
    # Export CSV
    exp_res_csv = client.post(f"/jobs/{job_id}/export", json={"format": "csv"})
    assert exp_res_csv.status_code == 200
    assert exp_res_csv.json()["format"] == "csv"
    assert "instruction,context,response" in exp_res_csv.json()["content"]
