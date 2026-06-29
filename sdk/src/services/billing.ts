import type { HttpClient } from '../core/http';

export interface BillingStatus {
  plan: string;
  search_quota_limit: number;
  search_used: number;
  subscription_status: string | null;
  current_period_end: string | null;
  stripe_configured: boolean;
}

export class BillingService {
  constructor(private http: HttpClient) {}

  async createCheckoutSession(plan: string): Promise<{ url: string }> {
    return this.http.post('/billing/checkout-session', { plan });
  }

  async createPortalSession(): Promise<{ url: string }> {
    return this.http.post('/billing/portal-session', {});
  }

  async getStatus(): Promise<BillingStatus> {
    return this.http.get('/billing/status');
  }
}
