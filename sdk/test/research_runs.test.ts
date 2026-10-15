import { describe, it, expect, vi } from "vitest";
import { CredenceAIClient } from "../src/client.js";

describe("ResearchRunsService SDK", () => {
  const mockFetch = vi.fn();

  const client = new CredenceAIClient({
    apiKey: "cred_sk_test_token_123",
    baseUrl: "https://api.credenceai.local",
    fetch: mockFetch,
  });

  it("creates a research run with proper payload", async () => {
    const mockRun = {
      id: "run_abc123",
      workspace_id: "ws_123",
      question: "Are solid state batteries production-ready?",
      mode: "investigate",
      status: "created",
      config_version: "v2.0",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      steps: [],
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => mockRun,
    });

    const run = await client.researchRuns.create({
      question: "Are solid state batteries production-ready?",
      mode: "investigate",
      idempotency_key: "idem_batt_1",
    });

    expect(run.id).toBe("run_abc123");
    expect(run.question).toBe("Are solid state batteries production-ready?");
    expect(mockFetch).toHaveBeenCalledWith(
      "https://api.credenceai.local/api/v2/research-runs",
      expect.objectContaining({
        method: "POST",
      })
    );
  });

  it("fetches claims and calibrated verdicts", async () => {
    const mockClaims = [
      {
        id: "clm_1",
        proposition: "Solid state batteries have reached 500 Wh/kg",
        units: "500 Wh/kg",
        origin_type: "user_submitted",
        verdict: "supported",
        rationale: "Corroborated by independent test laboratory reports.",
      },
    ];

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => mockClaims,
    });

    const claims = await client.researchRuns.getClaims("run_abc123");
    expect(claims.length).toBe(1);
    expect(claims[0].verdict).toBe("supported");
  });

  it("fetches frozen research brief with manifest hash", async () => {
    const mockReport = {
      id: "rpt_101",
      run_id: "run_abc123",
      workspace_id: "ws_123",
      version: 1,
      title: "Brief: Solid State Batteries",
      body_markdown: "# Brief [citation:pas_1001]",
      manifest_hash: "a".repeat(64),
      status: "frozen",
      created_at: new Date().toISOString(),
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => mockReport,
    });

    const report = await client.researchRuns.getReport("run_abc123", 1);
    expect(report.status).toBe("frozen");
    expect(report.manifest_hash.length).toBe(64);
  });

  it("submits human review annotation on evidence edge", async () => {
    const mockUpdatedEdge = {
      id: "edge_42",
      claim_id: "clm_1",
      passage_id: "pas_1001",
      relation: "supports",
      assessor_version: "v2.0",
      passage_text: "Lab test confirmed 500 Wh/kg cell performance.",
      reviewer_id: "usr_rev",
      reviewer_notes: "Expert validated laboratory methodology.",
      reviewed_at: new Date().toISOString(),
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => mockUpdatedEdge,
    });

    const updated = await client.researchRuns.reviewEvidence("run_abc123", "clm_1", "edge_42", {
      new_relation: "supports",
      reviewer_notes: "Expert validated laboratory methodology.",
    });

    expect(updated.relation).toBe("supports");
    expect(updated.reviewer_notes).toBe("Expert validated laboratory methodology.");
  });
});
