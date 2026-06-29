export interface CredenceAIConfig {
  baseUrl: string;
  apiKey?: string;
  apiPrefix?: string;
  timeoutMs?: number;
  pollIntervalMs?: number;
  maxWaitMs?: number;
  userAgent?: string;
  fetch?: typeof globalThis.fetch;
  getAccessToken?: () => string | null | Promise<string | null>;
}
