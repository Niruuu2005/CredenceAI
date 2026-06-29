import { HttpClient } from "../core/http.js";
import { HealthResponse } from "../types/index.js";

export class HealthService {
  constructor(private readonly http: HttpClient) {}

  async check(): Promise<HealthResponse> {
    return this.http.request<HealthResponse>({
      method: "GET",
      path: "/health",
    });
  }
}
