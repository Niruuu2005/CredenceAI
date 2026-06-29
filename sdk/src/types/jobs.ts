import { ApiErrorPayload } from "./common.js";

export interface CreateJobRequest {
  query?: string;
  input?: string;
  job_type?: string;
  priority?: string;
  vertical?: string;
  intent?: "news" | "company" | "research" | "web" | string;
  mode?: "fast" | "standard" | "deep" | string;
  metadata?: Record<string, unknown>;
}

export interface CreateJobResponse {
  job_id: string;
  status: string;
  trace_id?: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed" | string;
  result?: unknown;
  error?: ApiErrorPayload;
  trace_id?: string;
}
