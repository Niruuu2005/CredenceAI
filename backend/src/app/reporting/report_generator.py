"""
Citation-Validated Frozen Report Generator.
Implements FR-015, FR-016, Release Gate G7, RPT-01 to RPT-07.
Builds reproducible research briefs and validates 100% frozen citation resolution.
"""

import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import Report, ResearchRun, Passage, ClaimVerdict, utc_now
from app.reporting.citation_validator import CitationValidator, CitationResolutionError


class ReportGenerator:
    """
    Generates structured research briefs grounded in frozen citations.
    """

    @classmethod
    def generate_report_markdown(
        cls,
        run: ResearchRun,
        verdict: ClaimVerdict,
        passages: List[Passage],
        coverage_summary: Optional[str] = None,
    ) -> str:
        """
        Build markdown report embedding explicit citation anchors.
        """
        lines = [
            f"# Research Brief: {run.question}",
            "",
            f"**Verdict:** `{verdict.verdict.upper()}`  ",
            f"**Rationale:** {verdict.rationale}  ",
            f"**Run ID:** `{run.id}` | **Mode:** `{run.mode}`  ",
            "",
            "## Corroborating Evidence Passages",
            "",
        ]

        if not passages:
            lines.append("*No corroborating passages were retrieved within configured constraints.*")
        else:
            for idx, p in enumerate(passages, 1):
                clean_excerpt = p.text_content.strip().replace("\n", " ")
                if len(clean_excerpt) > 280:
                    clean_excerpt = f"{clean_excerpt[:280]}..."
                lines.append(f"{idx}. \"{clean_excerpt}\" [citation:{p.id}] (Passage: `{p.id}`)")

        lines.extend([
            "",
            "## Source Coverage & Methodology",
            coverage_summary or "- Multi-provider retrieval executed within workspace security boundaries.",
            "",
            "---",
            "*Calibration Disclaimer: Findings reflect evidence examined at retrieval time. Does not assert universal factual certainty.*",
        ])

        return "\n".join(lines)

    @classmethod
    def create_frozen_report(
        cls,
        db: Session,
        run: ResearchRun,
        verdict: ClaimVerdict,
        passages: List[Passage],
        coverage_summary: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Report:
        """
        Generate, validate through Gate G7, and persist frozen Report.
        """
        markdown = cls.generate_report_markdown(
            run=run,
            verdict=verdict,
            passages=passages,
            coverage_summary=coverage_summary,
        )

        # Release Gate G7: Enforce 100% frozen citation resolution
        manifest_hash = CitationValidator.enforce_gate_g7(db, markdown, expected_run_id=run.id)

        report = Report(
            id=f"rpt_{uuid.uuid4().hex[:12]}",
            run_id=run.id,
            workspace_id=run.workspace_id,
            version=1,
            title=title or f"Brief: {run.question[:60]}",
            body_markdown=markdown,
            manifest_hash=manifest_hash,
            status="frozen",
            created_at=utc_now(),
        )
        db.add(report)
        db.commit()
        return report
