"""
Human Review Annotation & Audit Service.
Implements FR-013, FR-014, BR-06, Gate G8.
Permits human researchers/reviewers to annotate or dispute evidence edges and approve reports.
Preserves immutable snapshots while recording reviewer decisions in AuditEvent log.
"""

import uuid
import json
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models import (
    ClaimEvidence,
    Report,
    ResearchRun,
    AuditEvent,
    utc_now,
)
from app.identity.auth_context import AuthContext, Permission
from app.evidence.relation_engine import VALID_RELATIONS


class ReviewPermissionError(Exception):
    """Raised when user lacks permission to perform human reviews."""
    pass


class ReviewService:
    """
    Manages human review annotations, overrides, and report approvals.
    """

    @classmethod
    def annotate_evidence(
        cls,
        db: Session,
        auth_context: AuthContext,
        evidence_id: str,
        new_relation: Optional[str] = None,
        reviewer_notes: Optional[str] = None,
    ) -> ClaimEvidence:
        """
        Annotate or override a ClaimEvidence edge.
        Immutable snapshots are never altered; changes are tracked via reviewer fields and audit events.
        """
        # Ensure user has review permission
        if not auth_context.has_permission(Permission.REVIEW_EVIDENCE) and not auth_context.has_permission(Permission.MANAGE_WORKSPACE):
            raise ReviewPermissionError("Current role does not possess permission to annotate evidence.")

        evidence = db.query(ClaimEvidence).filter(ClaimEvidence.id == evidence_id).first()
        if not evidence:
            raise ValueError(f"ClaimEvidence edge '{evidence_id}' not found.")

        old_relation = evidence.relation
        if new_relation:
            if new_relation not in VALID_RELATIONS:
                raise ValueError(f"Invalid relation '{new_relation}'. Must be one of {VALID_RELATIONS}")
            evidence.relation = new_relation

        evidence.reviewer_id = auth_context.user_id
        evidence.reviewer_notes = reviewer_notes
        evidence.reviewed_at = utc_now()

        # Record immutable audit event
        audit = AuditEvent(
            id=f"aud_{uuid.uuid4().hex[:12]}",
            workspace_id=auth_context.workspace_id,
            actor_id=auth_context.user_id,
            action="evidence.human_review",
            resource_type="claim_evidence",
            resource_id=evidence.id,
            details_json=json.dumps({
                "old_relation": old_relation,
                "new_relation": evidence.relation,
                "notes": reviewer_notes,
                "assessor_version": evidence.assessor_version,
            }),
            created_at=utc_now(),
        )
        db.add(audit)
        db.commit()
        db.refresh(evidence)
        return evidence

    @classmethod
    def approve_report(
        cls,
        db: Session,
        auth_context: AuthContext,
        report_id: str,
        reviewer_notes: Optional[str] = None,
    ) -> Report:
        """
        Review and approve a citation-frozen research report.
        """
        if not auth_context.has_permission(Permission.REVIEW_EVIDENCE) and not auth_context.has_permission(Permission.MANAGE_WORKSPACE):
            raise ReviewPermissionError("Current role does not possess permission to approve reports.")

        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise ValueError(f"Report '{report_id}' not found.")

        # Workspace boundary check
        if report.workspace_id != auth_context.workspace_id:
            raise ReviewPermissionError("Cross-workspace report review forbidden.")

        report.status = "approved"
        report.reviewed_by = auth_context.user_id
        report.reviewer_notes = reviewer_notes

        audit = AuditEvent(
            id=f"aud_{uuid.uuid4().hex[:12]}",
            workspace_id=auth_context.workspace_id,
            actor_id=auth_context.user_id,
            action="report.approved",
            resource_type="report",
            resource_id=report.id,
            details_json=json.dumps({
                "manifest_hash": report.manifest_hash,
                "version": report.version,
                "reviewer_notes": reviewer_notes,
            }),
            created_at=utc_now(),
        )
        db.add(audit)
        db.commit()
        db.refresh(report)
        return report
