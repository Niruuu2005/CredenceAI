export interface ApiErrorPayload {
  message: string;
  code?: string;
  details?: unknown;
}

export interface RunOptions {
  intent?: string;
  mode?: string;
  pollIntervalMs?: number;
  maxWaitMs?: number;
  metadata?: Record<string, unknown>;
}

export interface RunResult {
  jobId: string;
  status: string;
  data: unknown;
  traceId?: string;
}
