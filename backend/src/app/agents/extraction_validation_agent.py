"""
Extraction Validation Agent for CredenceAI Iteration 0.4 (Sprint 55)

Validates extracted document content for:
- Minimum quality thresholds (word count, token count, title presence)
- Language consistency
- Content completeness
- Duplicate / near-duplicate detection via hash comparison
- Schema compliance (required fields present)

Verdicts:
- valid: passes all quality gates
- warning: passes critical checks but has minor issues
- invalid: fails one or more critical checks
"""

import logging
import re
import hashlib
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class ValidationRule:
    """A single validation rule with severity level."""

    def __init__(self, name: str, critical: bool = False):
        self.name = name
        self.critical = critical  # True = failure causes invalid verdict


class ExtractionValidationReport(BaseModel):
    """Validation result for a single document."""
    url: str
    verdict: str  # "valid" | "warning" | "invalid"
    passed_rules: List[str] = Field(default_factory=list)
    failed_rules: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    quality_score: float = Field(ge=0.0, le=1.0, default=0.0)
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None


class BatchValidationOutput(BaseModel):
    """Output of batch document validation."""
    valid: List[str]       # URLs
    warnings: List[str]    # URLs
    invalid: List[str]     # URLs
    duplicates: List[str]  # URLs
    reports: List[ExtractionValidationReport]
    total_checked: int
    pass_rate: float = Field(ge=0.0, le=1.0)
    reasoning: str


class ExtractionValidationAgent(BaseAgent):
    """
    Agent that validates extracted document content against quality gates.

    Quality gates:
    - CRITICAL: has_text (document must have text content)
    - CRITICAL: min_word_count (>= 20 words)
    - CRITICAL: has_url (document must have URL)
    - WARNING: has_title (title should be present)
    - WARNING: min_token_count (>= 10 tokens)
    - WARNING: language_is_known (language code present)
    - WARNING: hash_present (content hash for dedup)
    """

    agent_name = "extraction_validation_agent"
    agent_description = "Validates extracted document content against quality gates and deduplicates"

    MIN_WORD_COUNT = 20
    MIN_TOKEN_COUNT = 10

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config=config or {})
        self._seen_hashes: Set[str] = set()  # for dedup within a batch

    def validate_input(self, agent_input: AgentInput) -> bool:
        if "documents" not in agent_input.context:
            raise ValueError("Missing required field: documents (list of extracted document dicts)")
        if not isinstance(agent_input.context["documents"], list):
            raise ValueError("documents must be a list")
        return True

    async def invoke(self, agent_input: AgentInput) -> AgentOutput:
        documents: List[Dict] = agent_input.context["documents"]
        reset_dedup: bool = agent_input.context.get("reset_dedup", True)

        if reset_dedup:
            self._seen_hashes.clear()

        valid_urls, warning_urls, invalid_urls, duplicate_urls = [], [], [], []
        reports = []

        for doc in documents:
            report = self._validate_document(doc)
            reports.append(report)
            if report.is_duplicate:
                duplicate_urls.append(report.url)
            if report.verdict == "valid":
                valid_urls.append(report.url)
            elif report.verdict == "warning":
                warning_urls.append(report.url)
            else:
                invalid_urls.append(report.url)

        total = len(documents)
        pass_rate = (len(valid_urls) + len(warning_urls)) / total if total > 0 else 0.0

        reasoning = (
            f"Validated {total} documents. "
            f"Valid: {len(valid_urls)}, Warning: {len(warning_urls)}, Invalid: {len(invalid_urls)}, "
            f"Duplicates: {len(duplicate_urls)}. Pass rate: {pass_rate:.1%}"
        )

        output = BatchValidationOutput(
            valid=valid_urls,
            warnings=warning_urls,
            invalid=invalid_urls,
            duplicates=duplicate_urls,
            reports=[r.model_dump() for r in reports],
            total_checked=total,
            pass_rate=round(pass_rate, 4),
            reasoning=reasoning,
        )

        return AgentOutput(
            decision=output.model_dump(),
            reasoning=reasoning,
            confidence_score=round(min(pass_rate + 0.05, 1.0), 4),
            metadata={
                "total": total,
                "valid": len(valid_urls),
                "warning": len(warning_urls),
                "invalid": len(invalid_urls),
                "duplicates": len(duplicate_urls),
            },
        )

    def parse_output(self, raw_output: Any) -> AgentOutput:
        if isinstance(raw_output, AgentOutput):
            return raw_output
        return AgentOutput(
            decision=str(raw_output),
            reasoning="Parsed from raw output",
            confidence_score=0.5,
        )

    # ──────────────────────────────────────────────
    # Validation logic
    # ──────────────────────────────────────────────

    def _validate_document(self, doc: Dict) -> ExtractionValidationReport:
        url = doc.get("url", "")
        text = doc.get("text", "") or ""
        title = doc.get("title", "") or ""
        language = doc.get("language", "") or ""
        word_count = doc.get("word_count") or len(text.split())
        token_count = doc.get("token_count") or (len(text) // 4)
        content_hash = doc.get("content_hash") or self._hash(text)

        passed, failed, warnings_list = [], [], []

        # ── Critical rules ──────────────────────────────
        if text.strip():
            passed.append("has_text")
        else:
            failed.append("has_text")

        if url.strip():
            passed.append("has_url")
        else:
            failed.append("has_url")

        if word_count >= self.MIN_WORD_COUNT:
            passed.append("min_word_count")
        else:
            failed.append(f"min_word_count({word_count}<{self.MIN_WORD_COUNT})")

        # ── Warning rules ───────────────────────────────
        if title.strip():
            passed.append("has_title")
        else:
            warnings_list.append("missing_title")

        if token_count >= self.MIN_TOKEN_COUNT:
            passed.append("min_token_count")
        else:
            warnings_list.append(f"low_token_count({token_count})")

        if language:
            passed.append("language_known")
        else:
            warnings_list.append("language_unknown")

        if content_hash:
            passed.append("hash_present")
        else:
            warnings_list.append("hash_missing")

        # ── Deduplication ────────────────────────────────
        is_duplicate = content_hash in self._seen_hashes
        duplicate_of = None
        if is_duplicate:
            duplicate_of = content_hash
        else:
            self._seen_hashes.add(content_hash)

        # ── Verdict ──────────────────────────────────────
        critical_failed = [f for f in failed if f in ("has_text", "has_url", "min_word_count")]
        if critical_failed:
            verdict = "invalid"
        elif warnings_list:
            verdict = "warning"
        else:
            verdict = "valid"

        quality_score = self._compute_quality_score(passed, failed, warnings_list, is_duplicate)

        return ExtractionValidationReport(
            url=url,
            verdict=verdict,
            passed_rules=passed,
            failed_rules=failed,
            warnings=warnings_list,
            quality_score=quality_score,
            is_duplicate=is_duplicate,
            duplicate_of=duplicate_of if is_duplicate else None,
        )

    @staticmethod
    def _compute_quality_score(
        passed: List[str], failed: List[str], warnings: List[str], is_duplicate: bool
    ) -> float:
        total_rules = len(passed) + len(failed) + len(warnings)
        if total_rules == 0:
            return 0.0
        score = len(passed) / total_rules
        if is_duplicate:
            score *= 0.5
        return round(max(0.0, min(1.0, score)), 4)

    @staticmethod
    def _hash(text: str) -> str:
        normalised = re.sub(r"\s+", " ", text).strip().lower()
        return hashlib.sha256(normalised.encode("utf-8")).hexdigest()

    def reset_dedup_state(self) -> None:
        """Manually clear dedup hash set between unrelated batches."""
        self._seen_hashes.clear()
