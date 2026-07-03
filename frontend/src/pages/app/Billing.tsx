import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, AlertCircle, Loader2, CreditCard } from "lucide-react";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { withWakeupRetry } from "@/lib/retry";
import { cn } from "@/lib/utils";

export function Billing() {
  const [user, setUser] = useState<{ plan: string; search_quota_limit: number; search_used?: number } | null>(null);
  const [billingStatus, setBillingStatus] = useState<{
    plan: string;
    search_quota_limit: number;
    search_used: number;
    subscription_status: string | null;
    current_period_end: string | null;
    stripe_configured: boolean;
  } | null>(null);
  const [jobCount, setJobCount] = useState(0);
  const [monitorsCount, setMonitorsCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const u = await withWakeupRetry(() => api.getCurrentUser());
      setUser(u as { plan: string; search_quota_limit: number; search_used?: number });
      setJobCount(u.search_used ?? 0);

      try {
        const status = await api.getBillingStatus();
        setBillingStatus(status);
        if (status.search_used !== undefined) {
          setJobCount(status.search_used);
        }
      } catch (e) {
        console.warn("Failed to fetch detailed billing status:", e);
        // Fallback billing state
        setBillingStatus({
          plan: u.plan,
          search_quota_limit: u.search_quota_limit,
          search_used: u.search_used ?? 0,
          subscription_status: null,
          current_period_end: null,
          stripe_configured: false,
        });
      }

      const monitors = await api.getMonitors();
      setMonitorsCount(monitors.length);
    } catch (err) {
      console.error("Failed to load billing data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleUpgrade = async (plan: string) => {
    setUpgrading(true);
    setMessage(null);
    try {
      try {
        const checkout = await api.createCheckoutSession(plan);
        if (checkout.url) {
          window.location.href = checkout.url;
          return;
        }
      } catch (err) {
        console.warn("Stripe checkout session failed:", err);
        if (import.meta.env.PROD) {
          setMessage(
            "Paid upgrades are not configured on this host deployment. The Free plan includes search and AI goal research."
          );
          return;
        }
      }
      const res = await api.upgradePlan(plan);
      setMessage(res.message);
      await fetchData();
    } catch (err: unknown) {
      console.error("Failed to upgrade plan:", err);
      setMessage(err instanceof Error ? err.message : "Failed to upgrade plan.");
    } finally {
      setUpgrading(false);
    }
  };

  const searchQuotaLimit = user?.search_quota_limit || 50;
  const monitorLimit = user?.plan === "Free" ? 1 : (user?.plan === "Pro" ? 10 : 100);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center bg-bg-deep text-text-body">
        <div className="flex items-center gap-3 text-sm text-text-subtle">
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
          <span>Loading billing and usage parameters...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl space-y-10 pb-12 bg-bg-deep text-text-body font-sans select-none">
      <div>
        <h2 className="text-3xl font-serif italic text-text-title mb-2">Billing & Plans</h2>
        <p className="text-[10px] uppercase tracking-widest font-extrabold text-text-subtle">Manage your subscription, usage, and payments.</p>
      </div>

      {message && (
        <div className="p-4 bg-teal-500/10 border-l-4 border-teal-500 text-teal-600 dark:text-teal-400 text-xs font-semibold rounded-xl flex items-center gap-2 animate-fade-in">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>{message}</span>
        </div>
      )}

      {/* Stripe Sandbox indicator */}
      {billingStatus?.stripe_configured === false && (
        <div className="p-4 bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 text-xs font-semibold rounded-2xl flex items-start gap-3 neu-inset-sm select-none">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5 text-amber-500" />
          <div>
            <p className="font-extrabold text-text-title">Billing Sandbox Mode</p>
            <p className="mt-1 leading-relaxed text-text-body font-normal">
              Stripe API integrations are not configured on this host deployment. Payment checkouts are simulated or require administrative configuration.
            </p>
          </div>
        </div>
      )}

      {/* Active Plan Detail Box */}
      <div className={cn(
        "rounded-2xl bg-bg-deep p-6 border-l-4 flex flex-col md:flex-row md:items-center justify-between gap-6 neu-outset select-none",
        user?.plan === "Free" ? "border-primary" : "border-highlight-color"
      )}>
        <div className="flex items-start gap-4">
          {user?.plan === "Free" ? (
            <AlertCircle className="h-6 w-6 text-primary shrink-0 mt-0.5" />
          ) : (
            <CheckCircle2 className="h-6 w-6 text-highlight-color shrink-0 mt-0.5" />
          )}
          <div>
            <div className="flex items-center gap-2.5">
              <h4 className="font-serif italic text-2xl text-text-title font-semibold">
                {user?.plan || "Free"} Plan
              </h4>
              <span className={cn(
                "text-[9px] uppercase tracking-widest px-2.5 py-0.5 rounded-full font-bold border",
                user?.plan === "Free" 
                  ? "bg-primary/10 text-primary border-primary/20" 
                  : "bg-highlight-color/10 text-highlight-color border-highlight-color/20"
              )}>
                Active
              </span>
            </div>
            <p className="text-xs text-text-subtle mt-1 font-semibold">
              {user?.plan === "Free" 
                ? "Standard search validation and intelligence research limits apply." 
                : "Thank you for supporting CredenceAI! Full workspace capabilities enabled."}
            </p>
          </div>
        </div>
        
        {/* Validity parameters */}
        <div className="flex flex-col md:items-end justify-center px-4 py-3 md:py-0 border-t md:border-t-0 md:border-l border-border-subtle/10 min-w-[200px]">
          <span className="text-[9px] uppercase tracking-widest text-text-subtle font-bold">Plan Validity</span>
          <span className="text-sm font-extrabold text-text-title mt-1 font-sans">
            {user?.plan === "Free" ? (
              "Perpetual (Resets Daily)"
            ) : billingStatus?.current_period_end ? (
              `Renews ${new Date(billingStatus.current_period_end).toLocaleDateString(undefined, {
                month: 'short',
                day: 'numeric',
                year: 'numeric'
              })}`
            ) : (
              "Active (Perpetual)"
            )}
          </span>
          {user?.plan !== "Free" && billingStatus?.subscription_status && (
            <span className="text-[8px] uppercase tracking-widest text-highlight-color font-bold mt-1">
              Status: {billingStatus.subscription_status}
            </span>
          )}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        {/* Usage Card */}
        <Card className="p-6">
          <CardHeader className="border-b border-border-subtle/10 pb-5 mb-5">
            <CardTitle className="text-xl font-serif italic text-text-title mb-1.5">Usage Summary</CardTitle>
            <CardDescription className="text-[10px] font-bold text-text-subtle">Resets daily at 00:00 UTC</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <div className="flex justify-between text-[10px] uppercase tracking-widest font-extrabold text-text-subtle mb-3">
                <span>Daily Search Jobs</span>
                <span className="font-mono text-text-title">{jobCount} / {searchQuotaLimit}</span>
              </div>
              <div className="h-4 w-full bg-bg-panel/40 rounded-full overflow-hidden neu-inset-sm border border-border-subtle/5 p-0.5">
                <div 
                  className="h-full bg-primary rounded-full transition-all duration-500 shadow-md" 
                  style={{ width: `${Math.min(100, (jobCount / searchQuotaLimit) * 100)}%` }}
                />
              </div>
              <span className="text-[8px] text-text-subtle block mt-1.5 font-bold uppercase tracking-wider">
                {searchQuotaLimit - jobCount} searches remaining today
              </span>
            </div>
            <div>
              <div className="flex justify-between text-[10px] uppercase tracking-widest font-extrabold text-text-subtle mb-3">
                <span>Active Continuous Monitors</span>
                <span className="font-mono text-text-title">{monitorsCount} / {monitorLimit}</span>
              </div>
              <div className="h-4 w-full bg-bg-panel/40 rounded-full overflow-hidden neu-inset-sm border border-border-subtle/5 p-0.5">
                <div 
                  className="h-full bg-primary rounded-full transition-all duration-500 shadow-md" 
                  style={{ width: `${Math.min(100, (monitorsCount / monitorLimit) * 100)}%` }}
                />
              </div>
              <span className="text-[8px] text-text-subtle block mt-1.5 font-bold uppercase tracking-wider">
                {monitorLimit - monitorsCount} monitor slots available
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Dynamic Billing Portal Action */}
        <Card className="p-6 flex flex-col justify-between">
          <CardHeader className="border-b border-border-subtle/10 pb-5 mb-5">
            <CardTitle className="text-xl font-serif italic text-text-title mb-1.5">Manage Payments</CardTitle>
            <CardDescription className="text-[10px] font-bold text-text-subtle">Stripe Integration Services</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-xs text-text-body leading-relaxed font-semibold">
              Update payment methods, view past invoices, or download receipts securely via the customer portal.
            </p>
            <div className="p-3.5 bg-bg-panel/20 rounded-xl border border-border-subtle/10 space-y-2">
              <div className="flex justify-between text-[10px] font-bold text-text-subtle">
                <span>Billing Provider:</span>
                <span className="text-text-body font-mono">Stripe Inc.</span>
              </div>
              <div className="flex justify-between text-[10px] font-bold text-text-subtle">
                <span>Sandbox Mode:</span>
                <span className={cn(
                  "font-mono font-bold",
                  billingStatus?.stripe_configured ? "text-highlight-color" : "text-amber-500"
                )}>
                  {billingStatus?.stripe_configured ? "No (Production Active)" : "Yes (Active)"}
                </span>
              </div>
            </div>
          </CardContent>
          <CardFooter className="pt-6">
            <Button 
              className="w-full h-10 rounded-xl"
              variant="outline"
              disabled={user?.plan === "Free" || upgrading}
              onClick={async () => {
                setUpgrading(true);
                try {
                  const portal = await api.createCheckoutSession(user?.plan || "Pro"); // Portal fallback to checkout
                  if (portal.url) window.location.href = portal.url;
                } catch (e) {
                  console.error(e);
                  setMessage("Stripe portal access is disabled or stripe pricing settings are unconfigured.");
                } finally {
                  setUpgrading(false);
                }
              }}
            >
              <CreditCard className="h-4 w-4 mr-2" />
              Access Billing Portal
            </Button>
          </CardFooter>
        </Card>
      </div>

      {/* Available plans comparing grid */}
      <div>
        <h3 className="text-2xl font-serif italic text-text-title mb-2">Available Workspace Tiers</h3>
        <p className="text-[10px] uppercase tracking-widest font-extrabold text-text-subtle mb-6">Select a plan to unlock additional scale, limits, and capabilities.</p>
        
        <div className="grid md:grid-cols-3 gap-8">
          {/* Free Card */}
          <Card className={cn(
            "p-6 flex flex-col justify-between transition-all duration-300 relative",
            user?.plan === "Free" ? "border border-primary" : "opacity-95"
          )}>
            {user?.plan === "Free" && (
              <div className="absolute top-0 right-0 bg-primary text-primary-foreground text-[8px] font-extrabold px-2.5 py-0.5 uppercase tracking-widest transform translate-x-2 -translate-y-2 rounded-md shadow-sm">
                Current Plan
              </div>
            )}
            <div className="space-y-6">
              <div className="border-b border-border-subtle/10 pb-5">
                <span className="text-[9px] uppercase tracking-widest font-extrabold text-text-subtle">Individual Tier</span>
                <h4 className="text-2xl font-serif italic text-text-title mt-1">Free Tier</h4>
                <p className="text-xs text-text-subtle mt-1.5 leading-relaxed">Basic search & validation features.</p>
              </div>
              <div className="space-y-4">
                <div className="text-4xl font-serif italic text-text-title font-medium">$0 <span className="text-xs text-text-subtle font-sans tracking-wide uppercase font-semibold">/ month</span></div>
                <ul className="space-y-3.5 pt-2">
                  <li className="flex items-center text-xs text-text-body">
                    <CheckCircle2 className="h-3.5 w-3.5 text-primary shrink-0 mr-3" />
                    <span className="font-semibold">50 searches / day</span>
                  </li>
                  <li className="flex items-center text-xs text-text-body">
                    <CheckCircle2 className="h-3.5 w-3.5 text-primary shrink-0 mr-3" />
                    <span className="font-semibold">1 Active Monitor</span>
                  </li>
                  <li className="flex items-center text-xs text-text-body">
                    <CheckCircle2 className="h-3.5 w-3.5 text-primary shrink-0 mr-3" />
                    <span className="font-semibold">Standard extraction logs</span>
                  </li>
                </ul>
              </div>
            </div>
            <div className="pt-8">
              <Button 
                className="w-full h-10 rounded-xl"
                variant="outline" 
                disabled
              >
                Current Plan
              </Button>
            </div>
          </Card>

          {/* Pro Card */}
          <Card className={cn(
            "p-6 flex flex-col justify-between transition-all duration-300 relative",
            user?.plan === "Pro" ? "border border-highlight-color shadow-[0_0_15px_rgba(16,185,129,0.15)]" : "border border-primary/20"
          )}>
            <div className="absolute top-0 right-0 bg-primary text-primary-foreground text-[8px] font-extrabold px-2.5 py-0.5 uppercase tracking-widest transform translate-x-2 -translate-y-2 rounded-md shadow-sm">
              {user?.plan === "Pro" ? "Current Plan" : "Recommended"}
            </div>
            <div className="space-y-6">
              <div className="border-b border-border-subtle/10 pb-5">
                <span className="text-[9px] uppercase tracking-widest font-extrabold text-primary">Intelligence Tier</span>
                <h4 className="text-2xl font-serif italic text-text-title mt-1">Pro Plan</h4>
                <p className="text-xs text-text-subtle mt-1.5 leading-relaxed">Continuous monitoring & deeper graphs.</p>
              </div>
              <div className="space-y-4">
                <div className="text-4xl font-serif italic text-text-title font-medium">$49 <span className="text-xs text-text-subtle font-sans tracking-wide uppercase font-semibold">/ month</span></div>
                <ul className="space-y-3.5 pt-2">
                  <li className="flex items-center text-xs text-text-body">
                    <CheckCircle2 className="h-3.5 w-3.5 text-primary shrink-0 mr-3" />
                    <span className="font-semibold">500 searches / day</span>
                  </li>
                  <li className="flex items-center text-xs text-text-body">
                    <CheckCircle2 className="h-3.5 w-3.5 text-primary shrink-0 mr-3" />
                    <span className="font-semibold">10 Active Monitors</span>
                  </li>
                  <li className="flex items-center text-xs text-text-body">
                    <CheckCircle2 className="h-3.5 w-3.5 text-primary shrink-0 mr-3" />
                    <span className="font-semibold">Up to 20 collections</span>
                  </li>
                </ul>
              </div>
            </div>
            <div className="pt-8">
              <Button 
                className="w-full h-10 rounded-xl"
                disabled={user?.plan === "Pro" || upgrading}
                onClick={() => handleUpgrade("Pro")}
              >
                {upgrading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                {user?.plan === "Pro" ? "Current Plan" : "Upgrade to Pro"}
              </Button>
            </div>
          </Card>

          {/* Enterprise Card */}
          <Card className={cn(
            "p-6 flex flex-col justify-between transition-all duration-300 relative",
            user?.plan === "Enterprise" ? "border border-highlight-color" : "border border-border-subtle/40"
          )}>
            {user?.plan === "Enterprise" && (
              <div className="absolute top-0 right-0 bg-primary text-primary-foreground text-[8px] font-extrabold px-2.5 py-0.5 uppercase tracking-widest transform translate-x-2 -translate-y-2 rounded-md shadow-sm">
                Current Plan
              </div>
            )}
            <div className="space-y-6">
              <div className="border-b border-border-subtle/10 pb-5">
                <span className="text-[9px] uppercase tracking-widest font-extrabold text-text-subtle">Corporate Tier</span>
                <h4 className="text-2xl font-serif italic text-text-title mt-1">Enterprise</h4>
                <p className="text-xs text-text-subtle mt-1.5 leading-relaxed">Dedicated infrastructure & scale.</p>
              </div>
              <div className="space-y-4">
                <div className="text-4xl font-serif italic text-text-title font-medium">Custom <span className="text-xs text-text-subtle font-sans tracking-wide uppercase font-semibold">/ pricing</span></div>
                <ul className="space-y-3.5 pt-2">
                  <li className="flex items-center text-xs text-text-body">
                    <CheckCircle2 className="h-3.5 w-3.5 text-primary shrink-0 mr-3" />
                    <span className="font-semibold">5,000 searches / day</span>
                  </li>
                  <li className="flex items-center text-xs text-text-body">
                    <CheckCircle2 className="h-3.5 w-3.5 text-primary shrink-0 mr-3" />
                    <span className="font-semibold">100 Active Monitors</span>
                  </li>
                  <li className="flex items-center text-xs text-text-body">
                    <CheckCircle2 className="h-3.5 w-3.5 text-primary shrink-0 mr-3" />
                    <span className="font-semibold">Unlimited collections</span>
                  </li>
                </ul>
              </div>
            </div>
            <div className="pt-8">
              <Button 
                className="w-full h-10 rounded-xl"
                variant="outline"
                disabled={user?.plan === "Enterprise" || upgrading}
                onClick={() => handleUpgrade("Enterprise")}
              >
                {user?.plan === "Enterprise" ? "Current Plan" : "Upgrade to Enterprise"}
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

