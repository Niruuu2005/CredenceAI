import { HttpClient } from "../core/http.js";
import { CreateJobRequest, CreateJobResponse, JobStatusResponse } from "../types/index.js";
import { ValidationError } from "../errors.js";

export class JobsService {
  constructor(private readonly http: HttpClient) {}

  async create(request: CreateJobRequest): Promise<CreateJobResponse> {
    const query = request?.query?.trim();
    const input = request?.input?.trim();
    if (!query && !input) {
      throw new ValidationError("createJob requires a non-empty query or input.");
    }

    return this.http.request<CreateJobResponse>({
      method: "POST",
      path: "/jobs",
      body: request,
    });
  }

  async list(limit: number = 20): Promise<JobStatusResponse[]> {
    return this.http.request<JobStatusResponse[]>({
      method: "GET",
      path: "/jobs",
      query: { limit },
    });
  }

  async get(jobId: string): Promise<JobStatusResponse> {
    if (!jobId?.trim()) {
      throw new ValidationError("getJob requires a valid jobId.");
    }

    return this.http.request<JobStatusResponse>({
      method: "GET",
      path: `/jobs/${encodeURIComponent(jobId)}`,
    });
  }
}
