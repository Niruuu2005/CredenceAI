import {
  ApiError,
  AuthenticationError,
  ValidationError,
  RateLimitError,
  NetworkError,
  TimeoutError,
} from "../errors.js";
import { DEFAULT_USER_AGENT, DEFAULT_RETRY_COUNT, DEFAULT_RETRY_BACKOFF_MS } from "../constants.js";
import { serializeQueryParams } from "./serializer.js";
import { sleep } from "../utils/timing.js";

export interface HttpClientConfig {
  baseUrl: string;
  apiPrefix?: string;
  apiKey?: string;
  timeoutMs: number;
  fetchImpl?: typeof globalThis.fetch;
  userAgent?: string;
  getAccessToken?: () => string | null | Promise<string | null>;
}

export interface HttpRequestOptions {
  method: "GET" | "POST" | "DELETE";
  path: string;
  query?: Record<string, string | number | boolean | undefined>;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  auth?: boolean;
}

export class HttpClient {
  private readonly baseUrl: string;
  private readonly apiPrefix: string;
  private readonly apiKey?: string;
  private readonly timeoutMs: number;
  private readonly fetchImpl: typeof globalThis.fetch;
  private readonly userAgent: string;
  private readonly getAccessToken?: () => string | null | Promise<string | null>;

  constructor(config: HttpClientConfig) {
    this.baseUrl = config.baseUrl;
    this.apiPrefix = config.apiPrefix ?? "";
    this.apiKey = config.apiKey;
    this.timeoutMs = config.timeoutMs;

    const globalFetch = typeof globalThis !== "undefined" ? globalThis.fetch : undefined;
    const defaultFetch = globalFetch
      ? globalFetch.bind(globalThis)
      : typeof fetch !== "undefined"
        ? fetch.bind(globalThis)
        : undefined;
    const resolvedFetch = config.fetchImpl ?? defaultFetch;
    if (!resolvedFetch) {
      throw new Error(
        "A fetch implementation is required. Please run in an environment with global fetch or pass a fetch polyfill."
      );
    }
    this.fetchImpl = resolvedFetch;
    this.userAgent = config.userAgent ?? DEFAULT_USER_AGENT;
    this.getAccessToken = config.getAccessToken;
  }

  async request<T>(options: HttpRequestOptions): Promise<T> {
    const prefix = this.apiPrefix.replace(/\/+$/, "");
    const path = options.path.startsWith("/") ? options.path : `/${options.path}`;
    const url = `${this.baseUrl}${prefix}${path}${serializeQueryParams(options.query)}`;

    const requestHeaders: Record<string, string> = {
      Accept: "application/json",
      "User-Agent": this.userAgent,
      ...options.headers,
    };

    if (options.body !== undefined) {
      requestHeaders["Content-Type"] = "application/json";
    }

    if (this.apiKey) {
      requestHeaders["X-API-Key"] = this.apiKey;
    }

    if (options.auth !== false && this.getAccessToken) {
      const token = await this.getAccessToken();
      if (token) {
        requestHeaders["Authorization"] = `Bearer ${token}`;
      }
    }

    let attempt = 0;
    const maxRetries = DEFAULT_RETRY_COUNT;

    while (attempt <= maxRetries) {
      const controller = new AbortController();
      const signal = options.signal
        ? this.linkSignals(options.signal, controller.signal)
        : controller.signal;

      const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

      try {
        const response = await this.fetchImpl(url, {
          method: options.method,
          headers: requestHeaders,
          body: options.body ? JSON.stringify(options.body) : undefined,
          signal,
        });

        clearTimeout(timeoutId);

        if (response.ok) {
          const contentType = response.headers.get("content-type") || "";
          if (contentType.includes("application/json")) {
            return (await response.json()) as T;
          }
          return (await response.text()) as unknown as T;
        }

        const statusCode = response.status;
        let errorPayload: any = null;
        try {
          const contentType = response.headers.get("content-type") || "";
          if (contentType.includes("application/json")) {
            errorPayload = await response.json();
          } else {
            errorPayload = { message: await response.text() };
          }
        } catch {
          // ignore parsing error
        }

        const traceId = errorPayload?.trace_id || response.headers.get("X-Trace-Id") || undefined;
        const errorMessage =
          errorPayload?.message ||
          errorPayload?.error?.message ||
          errorPayload?.detail ||
          `HTTP request failed with status ${statusCode}`;

        const isRetryable =
          statusCode === 429 || statusCode === 502 || statusCode === 503 || statusCode === 504;
        if (isRetryable && attempt < maxRetries) {
          attempt++;
          const backoff = this.calculateBackoff(attempt);
          await sleep(backoff);
          continue;
        }

        if (statusCode === 401 || statusCode === 403) {
          throw new AuthenticationError(errorMessage);
        } else if (statusCode === 400) {
          throw new ValidationError(errorMessage);
        } else if (statusCode === 429) {
          throw new RateLimitError(errorMessage, { statusCode, traceId, details: errorPayload });
        } else {
          throw new ApiError(errorMessage, { statusCode, traceId, details: errorPayload });
        }
      } catch (err: any) {
        clearTimeout(timeoutId);

        if (err.name === "AbortError" || signal.aborted) {
          if (options.signal?.aborted) {
            throw err;
          }
          throw new TimeoutError(`Request timed out after ${this.timeoutMs}ms`, {
            url,
            method: options.method,
          });
        }

        if (
          err instanceof ApiError ||
          err instanceof AuthenticationError ||
          err instanceof ValidationError
        ) {
          throw err;
        }

        if (attempt < maxRetries) {
          attempt++;
          const backoff = this.calculateBackoff(attempt);
          await sleep(backoff);
          continue;
        }

        throw new NetworkError(`Network connection failed: ${err.message}`, err);
      }
    }
    throw new NetworkError("Request failed: max retries exceeded");
  }

  private calculateBackoff(attempt: number): number {
    const base = DEFAULT_RETRY_BACKOFF_MS * Math.pow(2, attempt - 1);
    const jitter = (Math.random() - 0.5) * 0.5 * base;
    return Math.max(0, base + jitter);
  }

  private linkSignals(signal1: AbortSignal, signal2: AbortSignal): AbortSignal {
    const controller = new AbortController();
    const onAbort = () => controller.abort();

    if (signal1.aborted || signal2.aborted) {
      controller.abort();
      return controller.signal;
    }

    signal1.addEventListener("abort", onAbort);
    signal2.addEventListener("abort", onAbort);

    controller.signal.addEventListener("abort", () => {
      signal1.removeEventListener("abort", onAbort);
      signal2.removeEventListener("abort", onAbort);
    });

    return controller.signal;
  }
}
