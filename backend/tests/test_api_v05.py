import pytest
import uuid
from datetime import datetime, timezone
from app.models import Job, NormalizedResult, QualityScore, Entity, EntityLink, VerticalRun
from app.services.agent_decision_logger import AgentDecisionRecord

def test_list_jobs_and_filters(client, db_session):
    # Create some dummy jobs in the database
    job1 = Job(id="job_filter_1", trace_id="trace_1", job_type="search_query", input="test query one", status="completed", created_at=datetime.now(timezone.utc), user_id="mock_jane_doe")
    job2 = Job(id="job_filter_2", trace_id="trace_2", job_type="search_query", input="other search", status="failed", created_at=datetime.now(timezone.utc), user_id="mock_jane_doe")
    db_session.add(job1)
    db_session.add(job2)
    db_session.commit()

    # List jobs without filter
    res = client.get("/jobs")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 2
    
    # Filter by status
    res_status = client.get("/jobs?status=failed")
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert any(j["job_id"] == "job_filter_2" for j in data_status)
    assert not any(j["job_id"] == "job_filter_1" for j in data_status)

    # Filter by query search term
    res_q = client.get("/jobs?q=test")
    assert res_q.status_code == 200
    data_q = res_q.json()
    assert any(j["job_id"] == "job_filter_1" for j in data_q)
    assert not any(j["job_id"] == "job_filter_2" for j in data_q)


def test_get_job_results(client, db_session):
    # Setup database records with results, quality scores, and entity links
    job = Job(id="job_res_test", trace_id="trace_res", job_type="search_query", input="query text", status="completed", user_id="mock_jane_doe")
    db_session.add(job)
    
    # Normalized result
    res = NormalizedResult(
        id="res_1",
        job_id="job_res_test",
        source_result_id="src_1",
        title="Result title",
        url="https://example.com/res",
        source="google",
        language="en",
        fetched_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(res)
    db_session.commit()

    # Quality score
    qs = QualityScore(
        id="qs_1",
        result_id="res_1",
        final_trust_score=0.85,
        decision="accept",
        reason="Good source"
    )
    db_session.add(qs)
    
    # Entity and entity link
    ent = Entity(id="ent_1", canonical_name="Tesla", entity_type="organization", wikidata_id="Q1378")
    db_session.add(ent)
    db_session.commit()
    
    link = EntityLink(id="link_1", entity_id="ent_1", result_id="res_1", confidence=0.9)
    db_session.add(link)
    db_session.commit()

    # GET results
    response = client.get("/jobs/job_res_test/results")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert item["id"] == "res_1"
    assert item["quality_scores"]["final_trust_score"] == 0.85
    assert item["quality_scores"]["decision"] == "accept"
    assert len(item["entities"]) == 1
    assert item["entities"][0]["canonical_name"] == "Tesla"


def test_agent_decisions_endpoints(client, db_session):
    # Add dummy agent decision log record
    record = AgentDecisionRecord(
        job_id="job_agent_test",
        agent_name="PlannerAgent",
        input_data={"query": "test"},
        output_data={"plan": "step 1"},
        reasoning="Decided standard path",
        confidence_score=0.95,
        timestamp=datetime.now(timezone.utc),
        execution_time_ms=120,
        success=True
    )
    db_session.add(record)
    db_session.commit()

    # Query decisions list
    res = client.get("/agent/decisions")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    
    # Query by job
    res_job = client.get("/agent/decisions/job_agent_test")
    assert res_job.status_code == 200
    assert len(res_job.json()) == 1
    assert res_job.json()[0]["agent_name"] == "PlannerAgent"


def test_system_metrics(client, db_session):
    # Run GET /system/metrics
    res = client.get("/system/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "jobs_count" in data
    assert "results_count" in data
    assert "agent_decision_stats" in data
    assert "total_decisions" in data["agent_decision_stats"]


def test_evidence_and_intelligence_endpoints(client, db_session):
    # Setup entities, links, results for testing dynamic graph / cards
    ent = Entity(id="ent_ev_test", canonical_name="SpaceX", entity_type="organization", description="Space exploration company")
    db_session.add(ent)
    
    res = NormalizedResult(
        id="res_ev_1",
        job_id="job_ev_test",
        source_result_id="src_ev_1",
        title="SpaceX launched starship",
        url="https://spacex.com/starship",
        source="wikipedia",
        language="en",
        fetched_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        snippet="SpaceX launched its fifth Starship test flight successfully from Starbase Texas."
    )
    db_session.add(res)
    db_session.commit()

    link = EntityLink(id="link_ev_1", entity_id="ent_ev_test", result_id="res_ev_1", confidence=0.95)
    db_session.add(link)
    db_session.commit()

    # test GET /evidence/entities
    res_ents = client.get("/evidence/entities")
    assert res_ents.status_code == 200
    assert len(res_ents.json()) >= 1
    assert any(e["canonical_name"] == "SpaceX" for e in res_ents.json())

    # test GET /evidence/entities/{entity_id}/claims
    res_claims = client.get("/evidence/entities/ent_ev_test/claims")
    assert res_claims.status_code == 200
    claims_data = res_claims.json()
    assert len(claims_data) >= 1
    assert "SpaceX" in claims_data[0]["canonical_text"]

    # test GET /evidence/graph/{entity_id}
    res_graph = client.get("/evidence/graph/ent_ev_test")
    assert res_graph.status_code == 200
    graph_data = res_graph.json()
    assert "nodes" in graph_data
    assert "edges" in graph_data
    assert "summary" in graph_data

    # test GET /intelligence/card/{entity_id}
    res_card = client.get("/intelligence/card/ent_ev_test")
    assert res_card.status_code == 200
    card_data = res_card.json()
    assert card_data["entity_name"] == "SpaceX"
    assert card_data["source_count"] == 1
    assert len(card_data["key_facts"]) >= 1

    # test POST /intelligence/card/{entity_id}/refresh
    res_refresh = client.post("/intelligence/card/ent_ev_test/refresh")
    assert res_refresh.status_code == 200

    # test GET /intelligence/summary/{entity_id}
    res_sum = client.get("/intelligence/summary/ent_ev_test")
    assert res_sum.status_code == 200
    sum_data = res_sum.json()
    assert "summary" in sum_data
    assert "citations" in sum_data


def test_vertical_packs_endpoints(client, db_session):
    # test GET /verticals
    res = client.get("/verticals")
    assert res.status_code == 200
    packs = res.json()
    assert len(packs) == 4
    assert any(p["name"] == "company" for p in packs)
    assert any(p["name"] == "research" for p in packs)

    # test POST /verticals/company/run
    res_run = client.post("/verticals/company/run", json={"query": "Tesla EV competitors"})
    assert res_run.status_code == 202
    run_data = res_run.json()
    run_id = run_data.get("run_id")
    assert run_id
    assert run_data["status"] in ("completed", "running")

    # test GET /verticals/company/runs/{run_id}
    res_status = client.get(f"/verticals/company/runs/{run_id}")
    assert res_status.status_code == 200
    assert res_status.json()["run_id"] == run_id

    # test GET /verticals/company/runs/{run_id}/report (runs synchronous in test database)
    if res_status.json()["status"] == "completed":
        res_rep = client.get(f"/verticals/company/runs/{run_id}/report")
        assert res_rep.status_code == 200
        report = res_rep.json()
        assert report["pack_name"] == "Company Intelligence Pack"
        assert "company_profile" in report


def test_api_keys_monitors_collections(client, db_session):
    # 1. API Keys tests
    # Issue a key
    res = client.post("/auth/keys", json={"owner": "Test Owner", "label": "Test Key"})
    assert res.status_code == 201
    key_data = res.json()
    assert "key" in key_data
    assert key_data["owner"] == "mock_jane_doe"
    assert key_data["label"] == "Test Key"

    # List keys
    res_list = client.get("/auth/keys")
    assert res_list.status_code == 200
    keys = res_list.json()
    assert len(keys) >= 1
    target_key = [k for k in keys if k["label"] == "Test Key"][0]
    assert target_key["revoked"] is False

    # Revoke key
    res_revoke = client.delete(f"/auth/keys/{target_key['id']}")
    assert res_revoke.status_code == 200
    
    # List keys again (should be empty/no active keys)
    res_list2 = client.get("/auth/keys")
    assert res_list2.status_code == 200
    assert not any(k["id"] == target_key["id"] for k in res_list2.json())

    # 2. Monitors tests
    # Create monitor
    res_mon = client.post("/api/monitors", json={"topic": "AI Hardware"})
    assert res_mon.status_code == 201
    mon_data = res_mon.json()
    assert mon_data["topic"] == "AI Hardware"
    mon_id = mon_data["id"]

    # List monitors
    res_mon_list = client.get("/api/monitors")
    assert res_mon_list.status_code == 200
    assert any(m["id"] == mon_id for m in res_mon_list.json())

    # Sync monitor
    res_mon_sync = client.post(f"/api/monitors/{mon_id}/sync")
    assert res_mon_sync.status_code == 200
    assert res_mon_sync.json()["last_check"] == "Just now"

    # Delete monitor
    res_mon_del = client.delete(f"/api/monitors/{mon_id}")
    assert res_mon_del.status_code == 200

    # Verify deleted
    res_mon_list2 = client.get("/api/monitors")
    assert not any(m["id"] == mon_id for m in res_mon_list2.json())

    # 3. Collections tests
    # Create collection
    res_coll = client.post("/api/collections", json={"name": "Quantum Tech", "description": "Papers"})
    assert res_coll.status_code == 201
    coll_data = res_coll.json()
    assert coll_data["name"] == "Quantum Tech"
    coll_id = coll_data["id"]

    # List collections
    res_coll_list = client.get("/api/collections")
    assert res_coll_list.status_code == 200
    assert any(c["id"] == coll_id for c in res_coll_list.json())

    # Delete collection
    res_coll_del = client.delete(f"/api/collections/{coll_id}")
    assert res_coll_del.status_code == 200

    # Verify deleted
    res_coll_list2 = client.get("/api/collections")
    assert not any(c["id"] == coll_id for c in res_coll_list2.json())


def test_user_google_auth_and_security_headers(client, db_session):
    # 1. Test Google Auth URL endpoint
    res_url = client.get("/auth/google/url")
    assert res_url.status_code == 200
    url_data = res_url.json()
    assert "url" in url_data
    assert "mock" in url_data

    # 2. Test Callback exchange (Mock dev flow)
    res_callback = client.post("/auth/google/callback", json={"code": "mock_dev_code"})
    assert res_callback.status_code == 200
    callback_data = res_callback.json()
    assert "token" in callback_data
    assert callback_data["user"]["email"] == "jane.doe@example.com"
    token = callback_data["token"]

    # 3. Test Profile retrieval with JWT session token
    res_profile = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_profile.status_code == 200
    assert res_profile.json()["email"] == "jane.doe@example.com"
    assert res_profile.json()["name"] == "Jane Doe"

    # 4. Test unauthorized request rejection with invalid token
    res_invalid = client.get("/auth/me", headers={"Authorization": "Bearer invalid_session_jwt"})
    assert res_invalid.status_code == 401

    # 5. Verify Security Response Headers injection
    res_headers = client.get("/health")
    assert res_headers.status_code == 200
    headers = res_headers.headers
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in headers


