import { describe, it, expect } from "vitest";
import { validateApiKey } from "../src/core/validation.js";
import { redactApiKey } from "../src/core/auth.js";
import { AuthenticationError } from "../src/errors.js";

describe("API Key Authentication Validation", () => {
  it("should allow missing API key for session-based clients", () => {
    expect(() => validateApiKey(undefined)).not.toThrow();
    expect(() => validateApiKey("")).not.toThrow();
  });

  it("should throw AuthenticationError if API key is not a string", () => {
    expect(() => validateApiKey(null as any)).toThrow(AuthenticationError);
    expect(() => validateApiKey(12345 as any)).toThrow(AuthenticationError);
  });

  it("should throw AuthenticationError if API key does not start with cred_sk_", () => {
    expect(() => validateApiKey("sk_test_123456789")).toThrow(AuthenticationError);
    expect(() => validateApiKey("credsk_1234567890")).toThrow(AuthenticationError);
  });

  it("should throw AuthenticationError if API key is too short", () => {
    expect(() => validateApiKey("cred_sk_1")).toThrow(AuthenticationError);
    expect(() => validateApiKey("cred_sk_1234567")).toThrow(AuthenticationError);
  });

  it("should pass when API key is valid", () => {
    expect(() => validateApiKey("cred_sk_valid_api_key_123")).not.toThrow();
  });

  it("should redact API keys correctly", () => {
    expect(redactApiKey("short")).toBe("[REDACTED]");
    expect(redactApiKey("cred_sk_123456789abcdef")).toBe("cred_sk...cdef");
  });
});
