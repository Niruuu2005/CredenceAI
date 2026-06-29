import { HttpClient } from "../core/http.js";
import {
  ApiKeyRecord,
  AuthTokenResponse,
  CreateApiKeyResponse,
  GoogleAuthUrlResponse,
  UpgradePlanResponse,
  UserProfile,
} from "../types/auth.js";

export class AuthService {
  constructor(private readonly http: HttpClient) {}

  async getGoogleAuthUrl(): Promise<GoogleAuthUrlResponse> {
    return this.http.request<GoogleAuthUrlResponse>({
      method: "GET",
      path: "/auth/google/url",
      auth: false,
    });
  }

  async loginWithGoogle(code: string): Promise<AuthTokenResponse> {
    return this.http.request<AuthTokenResponse>({
      method: "POST",
      path: "/auth/google/callback",
      body: { code },
      auth: false,
    });
  }

  async loginWithCredentials(username: string, password: string): Promise<AuthTokenResponse> {
    return this.http.request<AuthTokenResponse>({
      method: "POST",
      path: "/auth/login",
      body: { username, password },
      auth: false,
    });
  }

  async getCurrentUser(): Promise<UserProfile> {
    return this.http.request<UserProfile>({
      method: "GET",
      path: "/auth/me",
    });
  }

  async upgradePlan(plan: string): Promise<UpgradePlanResponse> {
    return this.http.request<UpgradePlanResponse>({
      method: "POST",
      path: "/auth/upgrade",
      body: { plan },
    });
  }

  async listApiKeys(): Promise<ApiKeyRecord[]> {
    return this.http.request<ApiKeyRecord[]>({
      method: "GET",
      path: "/auth/keys",
    });
  }

  async createApiKey(label?: string): Promise<CreateApiKeyResponse> {
    return this.http.request<CreateApiKeyResponse>({
      method: "POST",
      path: "/auth/keys",
      body: { owner: "self", label },
    });
  }

  async revokeApiKey(keyId: number): Promise<{ message: string }> {
    return this.http.request<{ message: string }>({
      method: "DELETE",
      path: `/auth/keys/${keyId}`,
    });
  }
}
