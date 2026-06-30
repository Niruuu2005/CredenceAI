export interface UserProfile {
  id: string;
  email: string;
  name: string;
  picture: string | null;
  plan?: string;
  search_quota_limit?: number;
}

export interface AuthTokenResponse {
  token: string;
  user: UserProfile;
}

export interface GoogleAuthUrlResponse {
  url: string;
  mock: boolean;
}

export type GitHubAuthUrlResponse = GoogleAuthUrlResponse;

export interface UpgradePlanResponse {
  message: string;
  plan: string;
  search_quota_limit: number;
}

export interface ApiKeyRecord {
  id: number;
  owner: string;
  label: string | null;
  revoked: boolean;
  created_at: string;
  last_used_at: string | null;
}

export interface CreateApiKeyResponse {
  key: string;
  owner: string;
  label?: string;
  created_at: string;
}
