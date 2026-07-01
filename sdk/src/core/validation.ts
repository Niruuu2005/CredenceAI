import { ValidationError, AuthenticationError } from "../errors.js";

export function validateApiKey(apiKey?: string): void {
  if (apiKey === undefined || apiKey === "") {
    return;
  }

  if (typeof apiKey !== "string") {
    throw new AuthenticationError("Missing API key. Provide a valid CredenceAI API key.");
  }

  if (!apiKey.startsWith("cred_sk_")) {
    throw new AuthenticationError("Invalid API key format. Expected key starting with 'cred_sk_'.");
  }

  if (apiKey.length < 16) {
    throw new AuthenticationError("API key appears too short to be valid.");
  }
}

export function normalizeBaseUrl(baseUrl: string): string {
  if (typeof baseUrl !== "string") {
    throw new ValidationError("Base URL must be a string.");
  }
  const trimmed = baseUrl.trim();
  if (!trimmed) {
    // Empty base URL = same-origin relative paths (e.g. /api/health via Vercel proxy).
    return "";
  }
  try {
    new URL(trimmed);
  } catch {
    throw new ValidationError(
      `Invalid base URL: '${baseUrl}'. Must be a valid URL (e.g., 'http://127.0.0.1:8000' or 'https://api.yourdomain.com').`
    );
  }
  return trimmed.replace(/\/+$/, "");
}

export function validateTimeout(timeoutMs?: number): void {
  if (timeoutMs !== undefined) {
    if (typeof timeoutMs !== "number" || isNaN(timeoutMs) || timeoutMs <= 0) {
      throw new ValidationError("timeoutMs must be a positive number.");
    }
  }
}

export function validatePollInterval(pollIntervalMs?: number): void {
  if (pollIntervalMs !== undefined) {
    if (typeof pollIntervalMs !== "number" || isNaN(pollIntervalMs) || pollIntervalMs <= 0) {
      throw new ValidationError("pollIntervalMs must be a positive number.");
    }
  }
}
