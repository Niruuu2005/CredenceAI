import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { CredenceAIClient } from "../src/client.js";
import { AuthenticationError, ConfigurationError, ValidationError } from "../src/errors.js";

describe("CredenceAIClient Configuration", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    vi.resetModules();
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it("should initialize correctly with valid config options", () => {
    const client = new CredenceAIClient({
      apiKey: "cred_sk_valid_key_123",
      baseUrl: "https://api.example.com",
    });
    expect(client).toBeDefined();
  });

  it("should normalize base URL by removing trailing slashes", () => {
    const client = new CredenceAIClient({
      apiKey: "cred_sk_valid_key_123",
      baseUrl: "https://api.example.com///",
    });
    expect((client as any).baseUrl).toBe("https://api.example.com");
  });

  it("should throw ValidationError if baseUrl is empty or invalid format", () => {
    expect(
      () =>
        new CredenceAIClient({
          apiKey: "cred_sk_valid_key_123",
          baseUrl: "",
        })
    ).toThrow(ValidationError);

    expect(
      () =>
        new CredenceAIClient({
          apiKey: "cred_sk_valid_key_123",
          baseUrl: "not_a_valid_url",
        })
    ).toThrow(ValidationError);
  });

  it("should throw ValidationError if timeout values are negative or invalid", () => {
    expect(
      () =>
        new CredenceAIClient({
          apiKey: "cred_sk_valid_key_123",
          baseUrl: "https://api.example.com",
          timeoutMs: -10,
        })
    ).toThrow(ValidationError);
  });

  it("should initialize from environment variables via fromEnv", () => {
    process.env.CREDENCEAI_API_KEY = "cred_sk_valid_env_key";
    process.env.CREDENCEAI_BASE_URL = "https://env-api.example.com";

    const client = CredenceAIClient.fromEnv();
    expect(client).toBeDefined();
    expect((client as any).apiKey).toBe("cred_sk_valid_env_key");
    expect((client as any).baseUrl).toBe("https://env-api.example.com");
  });

  it("should throw AuthenticationError in fromEnv if apiKey is missing", () => {
    delete process.env.CREDENCEAI_API_KEY;
    process.env.CREDENCEAI_BASE_URL = "https://env-api.example.com";

    expect(() => CredenceAIClient.fromEnv()).toThrow(AuthenticationError);
  });

  it("should throw ConfigurationError in fromEnv if baseUrl is missing", () => {
    process.env.CREDENCEAI_API_KEY = "cred_sk_valid_env_key";
    delete process.env.CREDENCEAI_BASE_URL;

    expect(() => CredenceAIClient.fromEnv()).toThrow(ConfigurationError);
  });
});
