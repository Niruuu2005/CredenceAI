import { CredenceAIClient } from '@credenceai/sdk';

const TOKEN_KEY = 'cred_token';

function isVercelHost(): boolean {
  return (
    typeof window !== 'undefined' &&
    window.location.hostname.endsWith('.vercel.app')
  );
}

function sameOriginBaseUrl(): string {
  if (typeof window !== 'undefined') {
    return window.location.origin;
  }
  return 'http://localhost:8000';
}

function getApiBaseUrl(): string {
  // On Vercel, use same-origin /api (vercel.json rewrites to Render).
  if (isVercelHost()) {
    return sameOriginBaseUrl();
  }

  const configured = import.meta.env.VITE_API_BASE_URL as string | undefined;
  if (configured) {
    const trimmed = configured.trim();
    if (trimmed === '/api' || trimmed === '') {
      return sameOriginBaseUrl();
    }
    if (typeof window !== 'undefined' && /onrender\.com/i.test(trimmed)) {
      console.warn(
        '[CredenceAI] VITE_API_BASE_URL points at Render; using same-origin /api proxy instead.',
      );
      return sameOriginBaseUrl();
    }
    return trimmed.replace(/\/api\/?$/, '');
  }

  if (typeof window !== 'undefined') {
    return sameOriginBaseUrl();
  }
  return 'http://localhost:8000';
}

function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

const client = new CredenceAIClient({
  baseUrl: getApiBaseUrl(),
  apiPrefix: '/api',
  getAccessToken: () => getStoredToken(),
});

export interface JobResponse {
  job_id: string;
  status: string;
  job_type: string;
  input: string;
  submitted_at: string;
  completed_at: string | null;
  results_count: number;
  failed_events: number;
}

export interface GoalResponse {
  goal: string;
  plan_id: string;
  jobs: JobResponse[];
}

export interface SearchDocument {
  document_id: string;
  job_id: string;
  url: string;
  title: string;
  main_text: string;
  description: string;
  language: string;
  content_type: string;
  source: string;
  source_type: string;
  quality_score: number;
  extraction_quality_score: number;
  trusted: boolean;
  indexed_at: string | null;
  created_at: string | null;
  ranking_details?: {
    base_score: number;
    jaccard_similarity: number;
    phrase_boost: number;
    final_score: number;
    formula: string;
  };
}

export interface SearchResult {
  score: number;
  document: SearchDocument;
}

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchResult[];
}

export interface ApiKey {
  id: number;
  owner: string;
  label: string | null;
  revoked: boolean;
  created_at: string;
  last_used_at: string | null;
}

export interface Monitor {
  id: string;
  topic: string;
  scope: string;
  status: string;
  interval: string;
  lastCheck: string;
  health: string;
}

export interface Collection {
  id: string;
  name: string;
  description: string;
  itemsCount: number;
  updatedAt: string;
}

function mapJob(job: Record<string, unknown>): JobResponse {
  return {
    job_id: String(job.job_id ?? ''),
    status: String(job.status ?? ''),
    job_type: String(job.job_type ?? 'search_query'),
    input: String(job.input ?? ''),
    submitted_at: String(job.submitted_at ?? job.created_at ?? ''),
    completed_at: (job.completed_at as string | null) ?? null,
    results_count: Number(job.results_count ?? 0),
    failed_events: Number(job.failed_events ?? 0),
  };
}

function mapMonitor(m: { id: string; topic: string; scope: string; status: string; interval: string; last_check: string; health: string }): Monitor {
  return {
    id: m.id,
    topic: m.topic,
    scope: m.scope,
    status: m.status,
    interval: m.interval,
    lastCheck: m.last_check,
    health: m.health,
  };
}

function mapCollection(c: { id: string; name: string; description: string; items_count: number; updated_at: string }): Collection {
  return {
    id: c.id,
    name: c.name,
    description: c.description,
    itemsCount: c.items_count,
    updatedAt: new Date(c.updated_at).toLocaleDateString() + ' ' + new Date(c.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  };
}

function storeToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export const api = {
  async search(query: string, limit: number = 10): Promise<SearchResponse> {
    return client.search({ q: query, limit }) as Promise<SearchResponse>;
  },

  async submitJob(input: string, jobType: string = 'search_query', priority: string = 'normal'): Promise<JobResponse> {
    const res = await client.createJob({
      input,
      job_type: jobType,
      priority,
    });
    return mapJob(res as unknown as Record<string, unknown>);
  },

  async submitGoal(goal: string, vertical: string = 'general'): Promise<GoalResponse> {
    const res = await client.goals.submit({ goal, vertical });
    return {
      goal: res.goal,
      plan_id: res.plan_id,
      jobs: res.jobs.map((j) => mapJob(j as unknown as Record<string, unknown>)),
    };
  },

  async getJob(jobId: string): Promise<JobResponse> {
    const res = await client.getJob(jobId);
    return mapJob(res as unknown as Record<string, unknown>);
  },

  async getJobs(limit: number = 20): Promise<JobResponse[]> {
    const jobs = await client.listJobs(limit);
    return jobs.map((j) => mapJob(j as unknown as Record<string, unknown>));
  },

  async checkHealth(): Promise<{ status: string; service: string; version: string }> {
    const res = await client.health();
    return {
      status: String((res as { status?: string }).status ?? 'unknown'),
      service: String((res as { service?: string }).service ?? 'credenceai-api'),
      version: String((res as { version?: string }).version ?? ''),
    };
  },

  async getApiKeys(): Promise<ApiKey[]> {
    return client.auth.listApiKeys();
  },

  async createApiKey(label?: string) {
    return client.auth.createApiKey(label);
  },

  async revokeApiKey(keyId: number) {
    return client.auth.revokeApiKey(keyId);
  },

  async getMonitors(): Promise<Monitor[]> {
    const data = await client.monitors.list();
    return data.map(mapMonitor);
  },

  async createMonitor(topic: string, scope?: string, interval?: string): Promise<Monitor> {
    const m = await client.monitors.create({ topic, scope, interval });
    return mapMonitor(m);
  },

  async syncMonitor(monitorId: string): Promise<Monitor> {
    const m = await client.monitors.sync(monitorId);
    return mapMonitor(m);
  },

  async deleteMonitor(monitorId: string) {
    return client.monitors.delete(monitorId);
  },

  async getCollections(): Promise<Collection[]> {
    const data = await client.collections.list();
    return data.map(mapCollection);
  },

  async createCollection(name: string, description?: string): Promise<Collection> {
    const c = await client.collections.create({ name, description });
    return mapCollection(c);
  },

  async deleteCollection(collectionId: string) {
    return client.collections.delete(collectionId);
  },

  async getGoogleAuthUrl() {
    return client.auth.getGoogleAuthUrl();
  },

  async loginWithGoogle(code: string) {
    const data = await client.auth.loginWithGoogle(code);
    if (data.token) {
      storeToken(data.token);
    }
    return data;
  },

  async getGitHubAuthUrl() {
    return client.auth.getGitHubAuthUrl();
  },

  async loginWithGitHub(code: string) {
    const data = await client.auth.loginWithGitHub(code);
    if (data.token) {
      storeToken(data.token);
    }
    return data;
  },

  async loginWithCredentials(username: string, password: string) {
    const data = await client.auth.loginWithCredentials(username, password);
    if (data.token) {
      storeToken(data.token);
    }
    return data;
  },

  async upgradePlan(plan: string) {
    return client.auth.upgradePlan(plan);
  },

  async createCheckoutSession(plan: string): Promise<{ url: string }> {
    const res = await fetch(`${getApiBaseUrl()}/api/billing/checkout-session`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getStoredToken()}`,
      },
      body: JSON.stringify({ plan }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error((err as { detail?: string }).detail || 'Checkout failed');
    }
    return res.json();
  },

  async getBillingStatus() {
    const res = await fetch(`${getApiBaseUrl()}/api/billing/status`, {
      headers: { Authorization: `Bearer ${getStoredToken()}` },
    });
    if (!res.ok) throw new Error('Failed to load billing status');
    return res.json();
  },

  async getCurrentUser() {
    return client.auth.getCurrentUser();
  },

  logout() {
    localStorage.removeItem(TOKEN_KEY);
  },

  isAuthenticated(): boolean {
    return !!getStoredToken();
  },
};
