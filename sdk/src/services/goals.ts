import { HttpClient } from "../core/http.js";
import { JobStatusResponse } from "../types/jobs.js";

export interface GoalCreateRequest {
  goal: string;
  vertical?: string;
}

export interface GoalResponse {
  goal: string;
  plan_id: string;
  jobs: JobStatusResponse[];
}

export class GoalsService {
  constructor(private readonly http: HttpClient) {}

  async submit(request: GoalCreateRequest): Promise<GoalResponse> {
    return this.http.request<GoalResponse>({
      method: "POST",
      path: "/goals",
      body: request,
    });
  }
}
