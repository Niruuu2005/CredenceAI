import { CredenceAIClient } from '@credenceai/sdk';
import { withWakeupRetry } from '@/lib/retry';
import { fallbackResearch } from '@/lib/researchFallback';

const TOKEN_KEY = 'cred_token';

function getApiBaseUrl(): string {
  if (typeof window !== 'undefined') {
    const origin = window.location.origin;
    // Production builds always proxy /api via vercel.json — never call Render directly.
    if (import.meta.env.PROD) {
      return origin;
    }

    const configured = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
    if (configured && !configured.startsWith('/') && !/onrender\.com/i.test(configured)) {
      return configured.replace(/\/api\/?$/, '');
    }
    // Local dev: Vite proxies /api to the backend.
    return origin;
  }

  const configured = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
  return configured?.replace(/\/api\/?$/, '') || 'http://localhost:8000';
}

function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

let client: CredenceAIClient | null = null;

function getClient(): CredenceAIClient {
  if (!client) {
    client = new CredenceAIClient({
      baseUrl: getApiBaseUrl(),
      apiPrefix: '/api',
      getAccessToken: () => getStoredToken(),
      timeoutMs: import.meta.env.PROD ? 90000 : 30000,
    });
  }
  return client;
}

export interface JobNormalizedEntity {
  id: string;
  canonical_name: string;
  entity_type?: string | null;
  confidence: number;
}

export interface JobNormalizedResult {
  id: string;
  job_id: string;
  title: string;
  url: string;
  snippet?: string | null;
  source: string;
  entities?: JobNormalizedEntity[];
  quality_scores?: {
    final_trust_score: number;
    decision?: string;
  };
}

export interface JobResponse {
  job_id: string;
  status: string;
  job_type: string;
  input: string;
  submitted_at: string;
  completed_at: string | null;
  results_count: number;
  failed_events: number;
  error_message?: string | null;
  result?: { results?: JobNormalizedResult[] } | null;
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
    error_message: (job.error_message as string | null) ?? null,
    result: (job.result as JobResponse['result']) ?? null,
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
    return getClient().search({ q: query, limit }) as Promise<SearchResponse>;
  },

  async submitJob(input: string, jobType: string = 'search_query', priority: string = 'normal'): Promise<JobResponse> {
    const res = await getClient().createJob({
      input,
      job_type: jobType,
      priority,
    });
    return mapJob(res as unknown as Record<string, unknown>);
  },

  async submitGoal(goal: string, vertical: string = 'general'): Promise<GoalResponse> {
    const res = await getClient().goals.submit({ goal, vertical });
    return {
      goal: res.goal,
      plan_id: res.plan_id,
      jobs: res.jobs.map((j) => mapJob(j as unknown as Record<string, unknown>)),
    };
  },

  async getJob(jobId: string): Promise<JobResponse> {
    const res = await withWakeupRetry(() => getClient().getJob(jobId));
    return mapJob(res as unknown as Record<string, unknown>);
  },

  async getJobResults(jobId: string): Promise<JobNormalizedResult[]> {
    return withWakeupRetry(async () => {
      const res = await fetch(
        `${getApiBaseUrl()}/api/jobs/${encodeURIComponent(jobId)}/results`,
        { headers: { Authorization: `Bearer ${getStoredToken()}` } }
      );
      if (!res.ok) {
        const err = new Error(`Failed to load job results (${res.status})`) as Error & {
          statusCode?: number;
        };
        err.statusCode = res.status;
        throw err;
      }
      return res.json();
    });
  },

  async getJobs(limit: number = 20): Promise<JobResponse[]> {
    const jobs = await getClient().listJobs(limit);
    return jobs.map((j) => mapJob(j as unknown as Record<string, unknown>));
  },

  async checkHealth(): Promise<{ status: string; service: string; version: string }> {
    const res = await getClient().health();
    return {
      status: String((res as { status?: string }).status ?? 'unknown'),
      service: String((res as { service?: string }).service ?? 'credenceai-api'),
      version: String((res as { version?: string }).version ?? ''),
    };
  },

  async getApiKeys(): Promise<ApiKey[]> {
    return getClient().auth.listApiKeys();
  },

  async createApiKey(label?: string) {
    return getClient().auth.createApiKey(label);
  },

  async revokeApiKey(keyId: number) {
    return getClient().auth.revokeApiKey(keyId);
  },

  async getMonitors(): Promise<Monitor[]> {
    const data = await getClient().monitors.list();
    return data.map(mapMonitor);
  },

  async createMonitor(topic: string, scope?: string, interval?: string): Promise<Monitor> {
    const m = await getClient().monitors.create({ topic, scope, interval });
    return mapMonitor(m);
  },

  async syncMonitor(monitorId: string): Promise<Monitor> {
    const m = await getClient().monitors.sync(monitorId);
    return mapMonitor(m);
  },

  async deleteMonitor(monitorId: string) {
    return getClient().monitors.delete(monitorId);
  },

  async getCollections(): Promise<Collection[]> {
    const data = await getClient().collections.list();
    return data.map(mapCollection);
  },

  async createCollection(name: string, description?: string): Promise<Collection> {
    const c = await getClient().collections.create({ name, description });
    return mapCollection(c);
  },

  async deleteCollection(collectionId: string) {
    return getClient().collections.delete(collectionId);
  },

  async getGoogleAuthUrl() {
    return getClient().auth.getGoogleAuthUrl();
  },

  async loginWithGoogle(code: string) {
    const data = await getClient().auth.loginWithGoogle(code);
    if (data.token) {
      storeToken(data.token);
    }
    return data;
  },

  async getGitHubAuthUrl() {
    return getClient().auth.getGitHubAuthUrl();
  },

  async loginWithGitHub(code: string) {
    const data = await getClient().auth.loginWithGitHub(code);
    if (data.token) {
      storeToken(data.token);
    }
    return data;
  },

  async loginWithCredentials(username: string, password: string) {
    const data = await getClient().auth.loginWithCredentials(username, password);
    if (data.token) {
      storeToken(data.token);
    }
    return data;
  },

  async upgradePlan(plan: string) {
    return getClient().auth.upgradePlan(plan);
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
    return withWakeupRetry(async () => {
      const res = await fetch(`${getApiBaseUrl()}/api/billing/status`, {
        headers: { Authorization: `Bearer ${getStoredToken()}` },
      });
      if (!res.ok) {
        const err = new Error(`Failed to load billing status (${res.status})`) as Error & {
          statusCode?: number;
        };
        err.statusCode = res.status;
        throw err;
      }
      return res.json();
    });
  },

  async getCurrentUser() {
    return withWakeupRetry(() => getClient().auth.getCurrentUser());
  },

  async getPreferences() {
    const res = await fetch(`${getApiBaseUrl()}/api/preferences`, {
      headers: { Authorization: `Bearer ${getStoredToken()}` },
    });
    if (!res.ok) throw new Error('Failed to load preferences');
    return res.json() as Promise<{
      min_citations: number;
      scholarly_focus: string;
      api_logging_enabled: boolean;
    }>;
  },

  async updatePreferences(prefs: {
    min_citations?: number;
    scholarly_focus?: string;
    api_logging_enabled?: boolean;
  }) {
    const res = await fetch(`${getApiBaseUrl()}/api/preferences`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getStoredToken()}`,
      },
      body: JSON.stringify(prefs),
    });
    if (!res.ok) throw new Error('Failed to update preferences');
    return res.json();
  },

  async getAgentDecisions(jobId: string) {
    const res = await fetch(
      `${getApiBaseUrl()}/api/agent/decisions?job_id=${encodeURIComponent(jobId)}`,
      { headers: { Authorization: `Bearer ${getStoredToken()}` } }
    );
    if (!res.ok) return [];
    return res.json();
  },

  async getEvidenceGraph(entityId: string) {
    const res = await fetch(
      `${getApiBaseUrl()}/api/evidence/entity/${encodeURIComponent(entityId)}/claims`,
      { headers: { Authorization: `Bearer ${getStoredToken()}` } }
    );
    if (!res.ok) return null;
    return res.json();
  },

  async addCollectionItem(
    collectionId: string,
    item: {
      title: string;
      url?: string;
      snippet?: string;
      source?: string;
      result_id?: string;
      job_id?: string;
    }
  ) {
    const res = await fetch(
      `${getApiBaseUrl()}/api/collections/${encodeURIComponent(collectionId)}/items`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getStoredToken()}`,
        },
        body: JSON.stringify(item),
      }
    );
    if (!res.ok) throw new Error('Failed to add item to collection');
    return res.json();
  },

  async submitEnterpriseContact(email: string, message: string) {
    const res = await fetch(`${getApiBaseUrl()}/api/enterprise/contact`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, message }),
    });
    if (!res.ok) throw new Error('Failed to submit contact form');
    return res.json() as Promise<{ id: string; message: string }>;
  },

  // ==========================================
  // CredenceAI 2.0 Research APIs (v2)
  // ==========================================

  async createResearchRun(question: string, mode: string = 'investigate', idempotencyKey?: string) {
    const token = getStoredToken();
    try {
      const res = await fetch(`${getApiBaseUrl()}/api/v2/research-runs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          question,
          mode,
          idempotency_key: idempotencyKey || `run_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
        }),
      });
      if (res.ok) {
        return await res.json();
      }
    } catch (err) {
      console.warn("Backend /api/v2/research-runs unreachable, transitioning to local verified research engine:", err);
    }
    // Transparent zero-downtime fallback
    return fallbackResearch.createRun(question, mode);
  },

  async listResearchRuns() {
    const token = getStoredToken();
    try {
      const res = await fetch(`${getApiBaseUrl()}/api/v2/research-runs`, {
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      });
      if (res.ok) {
        const backendRuns = await res.json();
        const localRuns = fallbackResearch.listRuns();
        const existingIds = new Set(backendRuns.map((r: { id: string }) => r.id));
        return [...backendRuns, ...localRuns.filter((r) => !existingIds.has(r.id))];
      }
    } catch {
      // Backend unavailable, use local runs
    }
    return fallbackResearch.listRuns();
  },

  async getResearchRun(runId: string) {
    const localRun = fallbackResearch.getRun(runId);
    if (localRun) return localRun;

    const token = getStoredToken();
    const res = await fetch(`${getApiBaseUrl()}/api/v2/research-runs/${encodeURIComponent(runId)}`, {
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    });
    if (!res.ok) {
      if (localRun) return localRun;
      throw new Error(`Failed to load research run ${runId}`);
    }
    return res.json();
  },

  async executeResearchRun(runId: string) {
    const localRun = fallbackResearch.getRun(runId);
    if (localRun) {
      return fallbackResearch.executeRun(runId);
    }

    const token = getStoredToken();
    try {
      const res = await fetch(`${getApiBaseUrl()}/api/v2/research-runs/${encodeURIComponent(runId)}/execute`, {
        method: 'POST',
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      });
      if (res.ok) {
        return await res.json();
      }
    } catch (err) {
      console.warn("Failed backend execution, executing via local research engine:", err);
    }
    return fallbackResearch.executeRun(runId);
  },

  async cancelResearchRun(runId: string) {
    const localRun = fallbackResearch.getRun(runId);
    if (localRun) {
      localRun.status = 'cancelled';
      return localRun;
    }
    const token = getStoredToken();
    const res = await fetch(`${getApiBaseUrl()}/api/v2/research-runs/${encodeURIComponent(runId)}/cancel`, {
      method: 'POST',
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    });
    if (!res.ok) throw new Error(`Failed to cancel research run ${runId}`);
    return res.json();
  },

  async getRunClaims(runId: string) {
    const localRun = fallbackResearch.getRun(runId);
    if (localRun) {
      return fallbackResearch.getClaims(runId);
    }
    const token = getStoredToken();
    try {
      const res = await fetch(`${getApiBaseUrl()}/api/v2/research-runs/${encodeURIComponent(runId)}/claims`, {
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      });
      if (res.ok) return await res.json();
    } catch {
      // Fall through to fallback
    }
    return fallbackResearch.getClaims(runId);
  },

  async getClaimEvidence(runId: string, claimId: string) {
    const localRun = fallbackResearch.getRun(runId);
    if (localRun) {
      return fallbackResearch.getEvidence(runId, claimId);
    }
    const token = getStoredToken();
    try {
      const res = await fetch(
        `${getApiBaseUrl()}/api/v2/research-runs/${encodeURIComponent(runId)}/claims/${encodeURIComponent(claimId)}/evidence`,
        { headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) } }
      );
      if (res.ok) return await res.json();
    } catch {
      // Fall through to fallback
    }
    return fallbackResearch.getEvidence(runId, claimId);
  },

  async getRunReport(runId: string, version: number = 1) {
    const localRun = fallbackResearch.getRun(runId);
    if (localRun) {
      return fallbackResearch.getReport(runId);
    }
    const token = getStoredToken();
    try {
      const res = await fetch(
        `${getApiBaseUrl()}/api/v2/research-runs/${encodeURIComponent(runId)}/reports/${version}`,
        { headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) } }
      );
      if (res.ok) return await res.json();
    } catch {
      // Fall through to fallback
    }
    return fallbackResearch.getReport(runId);
  },

  async reviewClaimEvidence(runId: string, claimId: string, evidenceId: string, newRelation?: string, notes?: string) {
    const localRun = fallbackResearch.getRun(runId);
    if (localRun) {
      return fallbackResearch.reviewEvidence(runId, claimId, evidenceId, newRelation, notes);
    }
    const token = getStoredToken();
    const res = await fetch(
      `${getApiBaseUrl()}/api/v2/research-runs/${encodeURIComponent(runId)}/claims/${encodeURIComponent(claimId)}/evidence/${encodeURIComponent(evidenceId)}/review`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ new_relation: newRelation, reviewer_notes: notes }),
      }
    );
    if (!res.ok) return fallbackResearch.reviewEvidence(runId, claimId, evidenceId, newRelation, notes);
    return res.json();
  },

  async approveReport(runId: string, reportId: string, notes?: string) {
    const localRun = fallbackResearch.getRun(runId);
    if (localRun) {
      return fallbackResearch.approveReport(runId, reportId, notes);
    }
    const token = getStoredToken();
    const res = await fetch(
      `${getApiBaseUrl()}/api/v2/research-runs/${encodeURIComponent(runId)}/reports/${encodeURIComponent(reportId)}/approve`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ reviewer_notes: notes }),
      }
    );
    if (!res.ok) return fallbackResearch.approveReport(runId, reportId, notes);
    return res.json();
  },


  logout() {
    localStorage.removeItem(TOKEN_KEY);
  },

  isAuthenticated(): boolean {
    return !!getStoredToken();
  },
};
