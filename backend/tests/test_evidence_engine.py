"""
Evidence Engine, Passage Integrity & Frozen Reporting Test Suite.
Verifies Phase 2:
- Gate G5: Source Lineage & Syndication Deduplication (FR-011, DATA-03)
- Gate G6: 5-label Claim-Passage Relation Engine with Numeric/Temporal Checks (FR-010, EVD-05, EVD-07, EVD-08)
- Gate G7: Citation-Frozen Report Validation & AT-04 Zero Unanchored Citations (FR-015, FR-016, RPT-03)
- Gate G8: Human Review Auditability & SSRF Defense-in-Depth (FR-006, FR-014, BR-06)
"""

import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import (
    Base,
    Tenant,
    Workspace,
    User,
    Membership,
    Source,
    Snapshot,
    Passage,
    Claim,
    ClaimEvidence,
    ClaimVerdict,
    Report,
    AuditEvent,
    ResearchRun,
    utc_now,
)
from app.identity.auth_context import AuthContext, WorkspaceRole, ROLE_PERMISSIONS
from app.acquisition.ssrf_guard import SSRFGuard, SSRFSecurityException
from app.evidence.claim_extractor import extract_claims_from_text
from app.evidence.syndication_deduplicator import SyndicationDeduplicator, SourceCandidate
from app.evidence.relation_engine import (
    RelationEngine,
    RELATION_SUPPORTS,
    RELATION_CONTRADICTS,
    RELATION_MENTIONS,
    RELATION_IRRELEVANT,
    RELATION_UNCERTAIN,
)
from app.evidence.verdict_service import (
    VerdictService,
    VERDICT_SUPPORTED,
    VERDICT_DISPUTED,
    VERDICT_INSUFFICIENT_EVIDENCE,
)
from app.reporting.citation_validator import (
    CitationValidator,
    CitationResolutionError,
)
from app.reporting.report_generator import ReportGenerator
from app.evidence.review_service import ReviewService, ReviewPermissionError


@pytest.fixture
def evidence_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()

    tenant = Tenant(id="tenant_evd", name="Evidence Tenant")
    ws = Workspace(id="ws_evd", tenant_id="tenant_evd", name="Evidence Workspace")
    user_reviewer = User(id="user_rev", email="reviewer@firm.com", name="Reviewer One")
    user_viewer = User(id="user_vw", email="viewer@firm.com", name="Viewer One")
    mem_rev = Membership(id="mem_1", user_id="user_rev", workspace_id="ws_evd", role="reviewer")
    mem_vw = Membership(id="mem_2", user_id="user_vw", workspace_id="ws_evd", role="viewer")

    session.add_all([tenant, ws, user_reviewer, user_viewer, mem_rev, mem_vw])
    session.commit()

    yield session
    session.close()


def test_ssrf_guard_blocks_private_and_metadata_ips():
    """Verify SSRFGuard defends against RFC1918, loopback, and cloud metadata (NFR-009, Gate G8)."""
    blocked_ips = [
        "127.0.0.1",
        "10.0.0.5",
        "172.16.1.1",
        "192.168.1.100",
        "169.254.169.254",  # AWS/GCP/Azure instance metadata
        "::1",
    ]
    for ip in blocked_ips:
        assert SSRFGuard.is_private_or_restricted_ip(ip) is True

    # Public IP should not be blocked
    assert SSRFGuard.is_private_or_restricted_ip("8.8.8.8") is False

    with pytest.raises(SSRFSecurityException):
        SSRFGuard.validate_target_url("http://169.254.169.254/latest/meta-data/")

    with pytest.raises(SSRFSecurityException):
        SSRFGuard.validate_target_url("http://127.0.0.1:8080/admin")


def test_claim_extractor_atomic_propositions():
    """Verify decomposition into atomic propositions preserving origin and scope (FR-009, DATA-05)."""
    text = "In 2024, ACME Corp revenue grew by 15% across North America."
    drafts = extract_claims_from_text(text, origin_type="user_submitted")

    assert len(drafts) > 0
    assert drafts[0].temporal_scope == "2024"
    assert drafts[0].units == "15%"
    assert drafts[0].origin_type == "user_submitted"


def test_syndication_deduplication_wire_service_clustering():
    """Verify wire service republication grouping (FR-011, DATA-03, Gate G5)."""
    sources = [
        SourceCandidate(
            source_id="src_1",
            canonical_url="https://sitea.com/news/1",
            publisher="Site A",
            title="Tech Deal Signed",
            snippet="(Reuters) - ACME Corp acquired Beta Inc for $100M today.",
        ),
        SourceCandidate(
            source_id="src_2",
            canonical_url="https://siteb.com/biz/2",
            publisher="Site B",
            title="Tech Deal Signed",
            snippet="According to Reuters, ACME Corp acquired Beta Inc for $100M.",
        ),
        SourceCandidate(
            source_id="src_3",
            canonical_url="https://independent-blog.org/opinion",
            publisher="Independent Blog",
            title="Our Take on Beta Acquisition",
            snippet="Analysis on the $100M acquisition from industry analysts.",
        ),
    ]

    clusters = SyndicationDeduplicator.cluster_sources(sources)
    independent_count = SyndicationDeduplicator.get_independent_entity_count(clusters)

    # 3 articles, but 2 are syndicated from Reuters -> 2 independent publisher origins
    assert len(clusters) == 2
    assert independent_count == 2
    reuters_cluster = [c for c in clusters if c.wire_service == "Reuters"][0]
    assert len(reuters_cluster.members) == 2
    assert reuters_cluster.is_syndicated is True


def test_relation_engine_five_labels_and_sanity_checks():
    """Verify 5 typed relations and deterministic numeric/temporal sanity checks (FR-010, Gate G6)."""
    prop = "ACME revenue grew 15% in 2024"

    # 1. Direct Support
    support_pas = "Financial filings prove that ACME revenue grew 15% in 2024."
    res_sup = RelationEngine.evaluate(prop, support_pas)
    assert res_sup.relation == RELATION_SUPPORTS

    # 2. Contradiction: Numeric Mismatch (Claim 15% vs Passage 5%)
    num_mismatch_pas = "Audited figures indicate ACME revenue grew 5% in 2024."
    res_num = RelationEngine.evaluate(prop, num_mismatch_pas)
    assert res_num.relation == RELATION_CONTRADICTS
    assert any("Numeric discrepancy" in flag for flag in res_num.contradiction_flags)

    # 3. Contradiction: Temporal Mismatch (Claim 2024 vs Passage 2019)
    temp_mismatch_pas = "In 2019, ACME revenue grew 15% according to legacy reports."
    res_temp = RelationEngine.evaluate(prop, temp_mismatch_pas)
    assert res_temp.relation == RELATION_CONTRADICTS
    assert any("Temporal mismatch" in flag for flag in res_temp.contradiction_flags)

    # 4. Mentions: Topic present without affirmative confirmation
    mentions_pas = "The committee reviewed ACME revenue statements alongside competitor data."
    res_men = RelationEngine.evaluate(prop, mentions_pas)
    assert res_men.relation == RELATION_MENTIONS

    # 5. Irrelevant: Unrelated topic
    irrelevant_pas = "The James Webb Space Telescope detected ancient galaxies at high redshift."
    res_irr = RelationEngine.evaluate(prop, irrelevant_pas)
    assert res_irr.relation == RELATION_IRRELEVANT


def test_verdict_service_honest_abstention():
    """Verify run-scoped verdict aggregation and honest abstention (FR-012, EVD-10, EVD-12)."""
    # 1. Supported
    edge_sup = ClaimEvidence(
        id="e1", claim_id="c1", passage_id="p1", relation=RELATION_SUPPORTS
    )
    v_sup = VerdictService.aggregate_verdict([edge_sup], independent_sources_count=1)
    assert v_sup.verdict == VERDICT_SUPPORTED

    # 2. Disputed: Conflicting statements
    edge_contra = ClaimEvidence(
        id="e2", claim_id="c1", passage_id="p2", relation=RELATION_CONTRADICTS
    )
    v_disp = VerdictService.aggregate_verdict([edge_sup, edge_contra], independent_sources_count=2)
    assert v_disp.verdict == VERDICT_DISPUTED
    assert "Directly disputed" in v_disp.rationale

    # 3. Insufficient Evidence: Only mentions
    edge_mention = ClaimEvidence(
        id="e3", claim_id="c1", passage_id="p3", relation=RELATION_MENTIONS
    )
    v_insuf = VerdictService.aggregate_verdict([edge_mention], independent_sources_count=1)
    assert v_insuf.verdict == VERDICT_INSUFFICIENT_EVIDENCE


def test_gate_g7_citation_resolution_and_at_04(evidence_db):
    """
    Verify Gate G7 and AT-04:
    100% resolution required. Report with hallucinated/unanchored citation MUST fail.
    """
    # Create valid Source, Snapshot, Passage in DB
    src = Source(id="src_valid", canonical_url="https://sec.gov/filing", source_class="reference")
    evidence_db.add(src)
    evidence_db.flush()

    snap = Snapshot(
        id="snap_valid",
        source_id=src.id,
        content_hash="abc123hash",
        rights_status="fair_use_excerpt",
        fetched_at=utc_now(),
    )
    evidence_db.add(snap)
    evidence_db.flush()

    pas = Passage(
        id="pas_1001",
        snapshot_id=snap.id,
        text_content="Valid audited financial metrics.",
        passage_hash="hash_1001",
        extraction_version="v2.0",
    )
    evidence_db.add(pas)
    evidence_db.commit()

    # Valid report referencing pas_1001
    valid_markdown = (
        "# Valid Brief\n\n"
        "Revenue increased substantially. [citation:pas_1001] (Passage: `pas_1001`)"
    )
    manifest_hash = CitationValidator.enforce_gate_g7(evidence_db, valid_markdown)
    assert manifest_hash is not None
    assert len(manifest_hash) == 64

    # Invalid report referencing an unanchored hallucinated passage pas_9999
    invalid_markdown = (
        "# Invalid Brief\n\n"
        "Unsubstantiated hallucination. [citation:pas_9999_fake] (Passage: `pas_9999_fake`)"
    )
    with pytest.raises(CitationResolutionError) as exc_info:
        CitationValidator.enforce_gate_g7(evidence_db, invalid_markdown)

    assert "pas_9999_fake" in exc_info.value.unresolved_ids
    assert "Release Gate G7 Violated" in str(exc_info.value)


def test_human_review_preserves_immutable_snapshots_and_records_audit(evidence_db):
    """Verify human review annotation and audit trail (FR-013, FR-014, BR-06, Gate G8)."""
    # Create claim and evidence edge
    claim = Claim(
        id="clm_rev",
        workspace_id="ws_evd",
        proposition="New energy policy reduces emissions",
    )
    pas = Passage(
        id="pas_rev",
        snapshot_id="snap_rev",
        text_content="Policy documents discuss potential reduction trajectories.",
        passage_hash="hash_rev",
    )
    edge = ClaimEvidence(
        id="edge_rev_1",
        claim_id=claim.id,
        passage_id=pas.id,
        relation=RELATION_MENTIONS,
        assessor_version="v2.0",
    )
    report = Report(
        id="rpt_rev_1",
        run_id="run_test",
        workspace_id="ws_evd",
        title="Test Brief",
        body_markdown="Brief content [citation:pas_rev]",
        manifest_hash="hashmanifest",
        status="frozen",
    )
    evidence_db.add_all([claim, pas, edge, report])
    evidence_db.commit()

    # Reviewer auth context
    reviewer_ctx = AuthContext(
        user_id="user_rev",
        tenant_id="tenant_evd",
        workspace_id="ws_evd",
        role=WorkspaceRole.REVIEWER,
        permissions=ROLE_PERMISSIONS[WorkspaceRole.REVIEWER],
    )

    # 1. Reviewer annotates / disputes edge relation
    updated_edge = ReviewService.annotate_evidence(
        db=evidence_db,
        auth_context=reviewer_ctx,
        evidence_id=edge.id,
        new_relation=RELATION_SUPPORTS,
        reviewer_notes="Human expert verified this trajectory constitutes affirmative support.",
    )

    assert updated_edge.relation == RELATION_SUPPORTS
    assert updated_edge.reviewer_id == "user_rev"
    assert updated_edge.reviewed_at is not None

    # Verify original passage remains unchanged (BR-06)
    refreshed_pas = evidence_db.query(Passage).filter(Passage.id == "pas_rev").first()
    assert refreshed_pas.text_content == "Policy documents discuss potential reduction trajectories."

    # Verify AuditEvent was logged
    audit = (
        evidence_db.query(AuditEvent)
        .filter(AuditEvent.resource_id == edge.id, AuditEvent.action == "evidence.human_review")
        .first()
    )
    assert audit is not None
    assert audit.actor_id == "user_rev"
    assert "old_relation" in audit.details_json

    # 2. Reviewer approves report
    approved_report = ReviewService.approve_report(
        db=evidence_db,
        auth_context=reviewer_ctx,
        report_id=report.id,
        reviewer_notes="Approved for executive dissemination.",
    )
    assert approved_report.status == "approved"
    assert approved_report.reviewed_by == "user_rev"

    # 3. Viewer role should be denied review permission
    viewer_ctx = AuthContext(
        user_id="user_vw",
        tenant_id="tenant_evd",
        workspace_id="ws_evd",
        role=WorkspaceRole.VIEWER,
        permissions=ROLE_PERMISSIONS[WorkspaceRole.VIEWER],
    )
    with pytest.raises(ReviewPermissionError):
        ReviewService.annotate_evidence(
            db=evidence_db,
            auth_context=viewer_ctx,
            evidence_id=edge.id,
            new_relation=RELATION_CONTRADICTS,
        )
