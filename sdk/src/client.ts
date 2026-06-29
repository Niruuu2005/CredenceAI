import {
  CredenceAIConfig,
  CreateJobRequest,
  CreateJobResponse,
  JobStatusResponse,
  SearchQueryParams,
  SearchResponse,
  RunOptions,
  RunResult,
  HealthResponse,
} from "./types/index.js";
import { HttpClient } from "./core/http.js";
import { JobsService } from "./services/jobs.js";
import { SearchService } from "./services/search.js";
import { HealthService } from "./services/health.js";
import { AuthService } from "./services/auth.js";
import { MonitorsService } from "./services/monitors.js";
import { CollectionsService } from "./services/collections.js";
import { GoalsService } from "./services/goals.js";
import { BillingService } from "./services/billing.js";
import {
  validateApiKey,
  normalizeBaseUrl,
  validateTimeout,
  validatePollInterval,
} from "./core/validation.js";
import { getEnvVar } from "./utils/env.js";
import { ConfigurationError, AuthenticationError, JobFailedError, TimeoutError } from "./errors.js";
import { sleep } from "./utils/timing.js";
import { DEFAULT_TIMEOUT_MS, DEFAULT_POLL_INTERVAL_MS, DEFAULT_MAX_WAIT_MS } from "./constants.js";

export class CredenceAIClient {
  private readonly apiKey?: string;
  private readonly baseUrl: string;
  private readonly timeoutMs: number;
  private readonly pollIntervalMs: number;
  private readonly maxWaitMs: number;
  private readonly http: HttpClient;

  private readonly jobsService: JobsService;
  private readonly searchService: SearchService;
  private readonly healthService: HealthService;
  readonly auth: AuthService;
  readonly monitors: MonitorsService;
  readonly collections: CollectionsService;
  readonly goals: GoalsService;
  readonly billing: BillingService;

  constructor(config: CredenceAIConfig) {
    validateApiKey(config.apiKey);
    this.apiKey = config.apiKey;
    this.baseUrl = normalizeBaseUrl(config.baseUrl);

    validateTimeout(config.timeoutMs);
    this.timeoutMs = config.timeoutMs ?? DEFAULT_TIMEOUT_MS;

    validatePollInterval(config.pollIntervalMs);
    this.pollIntervalMs = config.pollIntervalMs ?? DEFAULT_POLL_INTERVAL_MS;

    validatePollInterval(config.maxWaitMs);
    this.maxWaitMs = config.maxWaitMs ?? DEFAULT_MAX_WAIT_MS;

    this.http = new HttpClient({
      baseUrl: this.baseUrl,
      apiPrefix: config.apiPrefix ?? "",
      apiKey: config.apiKey,
      timeoutMs: this.timeoutMs,
      fetchImpl: config.fetch,
      userAgent: config.userAgent,
      getAccessToken: config.getAccessToken,
    });

    this.jobsService = new JobsService(this.http);
    this.searchService = new SearchService(this.http);
    this.healthService = new HealthService(this.http);
    this.auth = new AuthService(this.http);
    this.monitors = new MonitorsService(this.http);
    this.collections = new CollectionsService(this.http);
    this.goals = new GoalsService(this.http);
    this.billing = new BillingService(this.http);
  }

  static fromEnv(
    opts: {
      baseUrl?: string;
      apiPrefix?: string;
      timeoutMs?: number;
      pollIntervalMs?: number;
      maxWaitMs?: number;
    } = {}
  ) {
    const apiKey = getEnvVar("CREDENCEAI_API_KEY");
    const baseUrl = opts.baseUrl ?? getEnvVar("CREDENCEAI_BASE_URL");

    if (!apiKey) {
      throw new AuthenticationError("Missing CREDENCEAI_API_KEY environment variable.");
    }

    if (!baseUrl) {
      throw new ConfigurationError(
        "Missing CredenceAI baseUrl. Provide it directly or via CREDENCEAI_BASE_URL."
      );
    }

    return new CredenceAIClient({
      apiKey,
      baseUrl,
      apiPrefix: opts.apiPrefix,
      timeoutMs: opts.timeoutMs,
      pollIntervalMs: opts.pollIntervalMs,
      maxWaitMs: opts.maxWaitMs,
    });
  }

  async health(): Promise<HealthResponse> {
    return this.healthService.check();
  }

  async createJob(request: CreateJobRequest): Promise<CreateJobResponse> {
    return this.jobsService.create(request);
  }

  async getJob(jobId: string): Promise<JobStatusResponse> {
    return this.jobsService.get(jobId);
  }

  async listJobs(limit: number = 20): Promise<JobStatusResponse[]> {
    return this.jobsService.list(limit);
  }

  async search(params: SearchQueryParams): Promise<SearchResponse> {
    return this.searchService.search(params);
  }

  async run(query: string, options: RunOptions = {}): Promise<RunResult> {
    const job = await this.createJob({
      query,
      intent: options.intent,
      mode: options.mode,
      metadata: options.metadata,
    });

    const pollInterval = options.pollIntervalMs ?? this.pollIntervalMs;
    const maxWait = options.maxWaitMs ?? this.maxWaitMs;
    const startedAt = Date.now();

    while (Date.now() - startedAt < maxWait) {
      const status = await this.getJob(job.job_id);

      if (status.status === "completed") {
        return {
          jobId: status.job_id,
          status: status.status,
          data: status.result,
          traceId: status.trace_id,
        };
      }

      if (status.status === "failed") {
        throw new JobFailedError(status.error?.message ?? "CredenceAI job failed.", {
          jobId: status.job_id,
          payload: status,
        });
      }

      await sleep(pollInterval);
    }

    throw new TimeoutError("CredenceAI job polling exceeded max wait time.", {
      query,
      maxWaitMs: maxWait,
      jobId: job.job_id,
    });
  }
}
