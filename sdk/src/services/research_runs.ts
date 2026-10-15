import { HttpClient } from "../core/http.js";
import {
  ResearchRun,
  CreateResearchRunOptions,
  ListResearchRunsOptions,
  SourceItem,
  Claim,
  EvidenceEdge,
  Report,
  EvidenceReviewInput,
  ReportApprovalInput,
} from "../types/research.js";
import { ValidationError } from "../errors.js";

export class ResearchRunsService {
  constructor(private readonly http: HttpClient) {}

  /**
   * Initiate a durable research run within caller's workspace.
   */
  async create(options: CreateResearchRunOptions): Promise<ResearchRun> {
    const question = options?.question?.trim();
    if (!question) {
      throw new ValidationError("createResearchRun requires a non-empty question proposition.");
    }

    return this.http.request<ResearchRun>({
      method: "POST",
      path: "/api/v2/research-runs",
      body: {
        question,
        mode: options.mode ?? "investigate",
        idempotency_key: options.idempotency_key,
        filters: options.filters ?? {},
        budget: options.budget ?? {},
      },
    });
  }

  /**
   * List runs scoped to caller's active workspace.
   */
  async list(options: ListResearchRunsOptions = {}): Promise<ResearchRun[]> {
    return this.http.request<ResearchRun[]>({
      method: "GET",
      path: "/api/v2/research-runs",
      query: {
        limit: options.limit ?? 50,
        offset: options.offset ?? 0,
      },
    });
  }

  /**
   * Retrieve run by ID with stage steps and timings.
   */
  async get(runId: string): Promise<ResearchRun> {
    if (!runId?.trim()) {
      throw new ValidationError("getResearchRun requires a valid runId.");
    }

    return this.http.request<ResearchRun>({
      method: "GET",
      path: `/api/v2/research-runs/${encodeURIComponent(runId)}`,
    });
  }

  /**
   * Directly execute a research run pipeline to completion.
   */
  async execute(runId: string): Promise<ResearchRun> {
    if (!runId?.trim()) {
      throw new ValidationError("executeResearchRun requires a valid runId.");
    }

    return this.http.request<ResearchRun>({
      method: "POST",
      path: `/api/v2/research-runs/${encodeURIComponent(runId)}/execute`,
    });
  }

  /**
   * Request graceful run cancellation at the next stage checkpoint.
   */
  async cancel(runId: string): Promise<ResearchRun> {
    if (!runId?.trim()) {
      throw new ValidationError("cancelResearchRun requires a valid runId.");
    }

    return this.http.request<ResearchRun>({
      method: "POST",
      path: `/api/v2/research-runs/${encodeURIComponent(runId)}/cancel`,
    });
  }

  /**
   * Retrieve sources acquired during the investigation.
   */
  async getSources(runId: string): Promise<SourceItem[]> {
    if (!runId?.trim()) {
      throw new ValidationError("getSources requires a valid runId.");
    }

    return this.http.request<SourceItem[]>({
      method: "GET",
      path: `/api/v2/research-runs/${encodeURIComponent(runId)}/sources`,
    });
  }

  /**
   * Retrieve atomic claims and verdicts evaluated for this run.
   */
  async getClaims(runId: string): Promise<Claim[]> {
    if (!runId?.trim()) {
      throw new ValidationError("getClaims requires a valid runId.");
    }

    return this.http.request<Claim[]>({
      method: "GET",
      path: `/api/v2/research-runs/${encodeURIComponent(runId)}/claims`,
    });
  }

  /**
   * Retrieve evidence grounding edges and passages for a specific claim.
   */
  async getEvidence(runId: string, claimId: string): Promise<EvidenceEdge[]> {
    if (!runId?.trim() || !claimId?.trim()) {
      throw new ValidationError("getEvidence requires valid runId and claimId.");
    }

    return this.http.request<EvidenceEdge[]>({
      method: "GET",
      path: `/api/v2/research-runs/${encodeURIComponent(runId)}/claims/${encodeURIComponent(claimId)}/evidence`,
    });
  }

  /**
   * Retrieve citation-frozen research brief.
   */
  async getReport(runId: string, version: number = 1): Promise<Report> {
    if (!runId?.trim()) {
      throw new ValidationError("getReport requires a valid runId.");
    }

    return this.http.request<Report>({
      method: "GET",
      path: `/api/v2/research-runs/${encodeURIComponent(runId)}/reports/${version}`,
    });
  }

  /**
   * Human review annotation or dispute of an evidence relation edge.
   */
  async reviewEvidence(
    runId: string,
    claimId: string,
    evidenceId: string,
    review: EvidenceReviewInput
  ): Promise<EvidenceEdge> {
    if (!runId?.trim() || !claimId?.trim() || !evidenceId?.trim()) {
      throw new ValidationError("reviewEvidence requires valid runId, claimId, and evidenceId.");
    }

    return this.http.request<EvidenceEdge>({
      method: "POST",
      path: `/api/v2/research-runs/${encodeURIComponent(runId)}/claims/${encodeURIComponent(claimId)}/evidence/${encodeURIComponent(evidenceId)}/review`,
      body: review,
    });
  }

  /**
   * Human reviewer approval of a frozen research report.
   */
  async approveReport(
    runId: string,
    reportId: string,
    input: ReportApprovalInput = {}
  ): Promise<Report> {
    if (!runId?.trim() || !reportId?.trim()) {
      throw new ValidationError("approveReport requires valid runId and reportId.");
    }

    return this.http.request<Report>({
      method: "POST",
      path: `/api/v2/research-runs/${encodeURIComponent(runId)}/reports/${encodeURIComponent(reportId)}/approve`,
      body: input,
    });
  }
}
