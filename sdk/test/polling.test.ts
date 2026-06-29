import { describe, it, expect, vi } from "vitest";
import { CredenceAIClient } from "../src/client.js";
import { JobFailedError, TimeoutError } from "../src/errors.js";

describe("CredenceAIClient Endpoint & Polling Tests", () => {
  const apiKey = "cred_sk_test_key_123456";
  const baseUrl = "https://api.example.com";

  it("should successfully execute health check", async () => {
    const mockResponse = { status: "ok", version: "0.1.0" };
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ "Content-Type": "application/json" }),
      json: async () => mockResponse,
    });

    const client = new CredenceAIClient({ apiKey, baseUrl, fetch: mockFetch });
    const health = await client.health();

    expect(health).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockFetch).toHaveBeenCalledWith(
      "https://api.example.com/health",
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({
          "X-API-Key": apiKey,
        }),
      })
    );
  });

  it("should successfully create job", async () => {
    const mockResponse = { job_id: "job-123", status: "queued" };
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ "Content-Type": "application/json" }),
      json: async () => mockResponse,
    });

    const client = new CredenceAIClient({ apiKey, baseUrl, fetch: mockFetch });
    const res = await client.createJob({ query: "test query", intent: "news" });

    expect(res).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith(
      "https://api.example.com/jobs",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ query: "test query", intent: "news" }),
      })
    );
  });

  it("should successfully retrieve job status", async () => {
    const mockResponse = { job_id: "job-123", status: "running" };
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ "Content-Type": "application/json" }),
      json: async () => mockResponse,
    });

    const client = new CredenceAIClient({ apiKey, baseUrl, fetch: mockFetch });
    const status = await client.getJob("job-123");

    expect(status).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith(
      "https://api.example.com/jobs/job-123",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("should successfully execute search query", async () => {
    const mockResponse = { query: "crypto", results: [{ title: "Bitcoin" }] };
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ "Content-Type": "application/json" }),
      json: async () => mockResponse,
    });

    const client = new CredenceAIClient({ apiKey, baseUrl, fetch: mockFetch });
    const searchRes = await client.search({ q: "crypto", limit: 5 });

    expect(searchRes).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith(
      "https://api.example.com/search?q=crypto&limit=5",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("should run blocking run() and poll until completed", async () => {
    let requestCount = 0;
    const mockFetch = vi.fn().mockImplementation(async (url, opts) => {
      requestCount++;
      if (url.endsWith("/jobs") && opts.method === "POST") {
        return {
          ok: true,
          headers: new Headers({ "Content-Type": "application/json" }),
          json: async () => ({ job_id: "job-123", status: "queued" }),
        };
      }
      if (url.endsWith("/jobs/job-123") && opts.method === "GET") {
        let status = "queued";
        let result = undefined;
        if (requestCount === 3) {
          status = "running";
        } else if (requestCount === 4) {
          status = "completed";
          result = { answer: "42" };
        }
        return {
          ok: true,
          headers: new Headers({ "Content-Type": "application/json" }),
          json: async () => ({ job_id: "job-123", status, result, trace_id: "trace-abc" }),
        };
      }
      return { ok: false, status: 404 };
    });

    const client = new CredenceAIClient({
      apiKey,
      baseUrl,
      fetch: mockFetch,
      pollIntervalMs: 1,
    });

    const runResult = await client.run("what is life?", { pollIntervalMs: 1 });
    expect(runResult).toEqual({
      jobId: "job-123",
      status: "completed",
      data: { answer: "42" },
      traceId: "trace-abc",
    });
    expect(requestCount).toBe(4);
  });

  it("should throw JobFailedError if job fails", async () => {
    const mockFetch = vi.fn().mockImplementation(async (url, opts) => {
      if (url.endsWith("/jobs") && opts.method === "POST") {
        return {
          ok: true,
          headers: new Headers({ "Content-Type": "application/json" }),
          json: async () => ({ job_id: "job-123", status: "queued" }),
        };
      }
      if (url.endsWith("/jobs/job-123") && opts.method === "GET") {
        return {
          ok: true,
          headers: new Headers({ "Content-Type": "application/json" }),
          json: async () => ({
            job_id: "job-123",
            status: "failed",
            error: { message: "Internal Celery Error" },
          }),
        };
      }
      return { ok: false, status: 404 };
    });

    const client = new CredenceAIClient({
      apiKey,
      baseUrl,
      fetch: mockFetch,
      pollIntervalMs: 1,
    });

    await expect(client.run("throw error", { pollIntervalMs: 1 })).rejects.toThrow(JobFailedError);
  });

  it("should throw TimeoutError if polling exceeds maxWaitMs", async () => {
    const mockFetch = vi.fn().mockImplementation(async (url, opts) => {
      if (url.endsWith("/jobs") && opts.method === "POST") {
        return {
          ok: true,
          headers: new Headers({ "Content-Type": "application/json" }),
          json: async () => ({ job_id: "job-123", status: "queued" }),
        };
      }
      if (url.endsWith("/jobs/job-123") && opts.method === "GET") {
        return {
          ok: true,
          headers: new Headers({ "Content-Type": "application/json" }),
          json: async () => ({ job_id: "job-123", status: "running" }),
        };
      }
      return { ok: false, status: 404 };
    });

    const client = new CredenceAIClient({
      apiKey,
      baseUrl,
      fetch: mockFetch,
      pollIntervalMs: 1,
      maxWaitMs: 5,
    });

    await expect(client.run("timeout please", { pollIntervalMs: 1, maxWaitMs: 5 })).rejects.toThrow(
      TimeoutError
    );
  });
});
