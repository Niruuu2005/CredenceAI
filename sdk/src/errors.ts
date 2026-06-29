export class CredenceAIError extends Error {
  constructor(message: string) {
    super(message);
    this.name = this.constructor.name;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class ConfigurationError extends CredenceAIError {}
export class AuthenticationError extends CredenceAIError {}
export class ValidationError extends CredenceAIError {}

export class ApiError extends CredenceAIError {
  statusCode?: number;
  traceId?: string;
  details?: unknown;

  constructor(
    message: string,
    options?: { statusCode?: number; traceId?: string; details?: unknown }
  ) {
    super(message);
    this.statusCode = options?.statusCode;
    this.traceId = options?.traceId;
    this.details = options?.details;
  }
}

export class TimeoutError extends CredenceAIError {
  details?: unknown;

  constructor(message: string, details?: unknown) {
    super(message);
    this.details = details;
  }
}

export class JobFailedError extends CredenceAIError {
  details?: unknown;

  constructor(message: string, details?: unknown) {
    super(message);
    this.details = details;
  }
}

export class RateLimitError extends ApiError {}

export class NetworkError extends CredenceAIError {
  originalError?: Error;

  constructor(message: string, originalError?: Error) {
    super(message);
    this.originalError = originalError;
  }
}
