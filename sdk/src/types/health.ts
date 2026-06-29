export interface HealthResponse {
  status: string;
  version?: string;
  dependencies?: Record<string, string>;
}
