export type ResearchMode = "discover" | "investigate" | "deep_investigation";

export type ResearchRunStatus =
  | "created"
  | "queued"
  | "planning"
  | "retrieving"
  | "extracting"
  | "verifying"
  | "reporting"
  | "completed"
  | "partial"
  | "failed"
  | "cancelled"
  | "timed_out";

export type EvidenceRelation = "supports" | "contradicts" | "mentions" | "irrelevant" | "uncertain";

export type ClaimVerdictType = "supported" | "disputed" | "insufficient_evidence" | "not_assessed";

export interface RunStep {
  id: string;
  step_key: string;
  state: string;
  attempt_count: number;
  duration_ms: number;
  error_type?: string | null;
  error_message?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface ResearchRun {
  id: string;
  workspace_id: string;
  question: string;
  mode: ResearchMode;
  status: ResearchRunStatus;
  config_version: string;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
  steps: RunStep[];
}

export interface CreateResearchRunOptions {
  question: string;
  mode?: ResearchMode;
  idempotency_key?: string;
  filters?: Record<string, any>;
  budget?: Record<string, any>;
}

export interface ListResearchRunsOptions {
  limit?: number;
  offset?: number;
}

export interface SourceItem {
  id: string;
  canonical_url: string;
  publisher?: string | null;
  source_class: string;
  syndication_upstream_id?: string | null;
}

export interface Claim {
  id: string;
  proposition: string;
  subject?: string | null;
  predicate?: string | null;
  object_val?: string | null;
  units?: string | null;
  temporal_scope?: string | null;
  geographic_scope?: string | null;
  origin_type: string;
  verdict?: ClaimVerdictType | null;
  rationale?: string | null;
}

export interface EvidenceEdge {
  id: string;
  claim_id: string;
  passage_id: string;
  relation: EvidenceRelation;
  rationale?: string | null;
  assessor_version: string;
  passage_text: string;
  publisher?: string | null;
  canonical_url?: string | null;
  reviewer_id?: string | null;
  reviewer_notes?: string | null;
  reviewed_at?: string | null;
}

export interface Report {
  id: string;
  run_id: string;
  workspace_id: string;
  version: number;
  title: string;
  body_markdown: string;
  manifest_hash: string;
  status: "draft" | "approved" | "frozen";
  reviewed_by?: string | null;
  reviewer_notes?: string | null;
  created_at: string;
}

export interface EvidenceReviewInput {
  new_relation?: EvidenceRelation;
  reviewer_notes?: string;
}

export interface ReportApprovalInput {
  reviewer_notes?: string;
}
