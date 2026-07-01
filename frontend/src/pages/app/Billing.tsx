import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";

export function Billing() {
  const [user, setUser] = useState<{ plan: string; search_quota_limit: number } | null>(null);
  const [jobCount, setJobCount] = useState(0);
  const [monitorsCount, setMonitorsCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const u = await api.getCurrentUser();
      setUser(u as any);
      
      const jobs = await api.getJobs(100);
      setJobCount(jobs.length);

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
      } catch {
        if (import.meta.env.PROD) {
          setMessage(
            "Paid upgrades are not configured on this deployment. The Free plan includes search and AI goal research."
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
          <Loader2 className="h-5 w-5 animate-spin text-highlight-color" />
          <span>Loading billing and usage parameters...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto pr-2 max-w-4xl space-y-12 pb-12 bg-bg-deep text-text-body">
      <div>
        <h2 className="text-3xl font-serif italic text-text-title mb-2">Billing & Plans</h2>
        <p className="text-[10px] uppercase tracking-widest font-medium text-text-subtle">Manage your subscription, usage, and payments.</p>
      </div>

      {message && (
        <div className="bg-emerald-950/20 border border-emerald-500/30 p-4 text-emerald-500 text-xs font-semibold uppercase tracking-wider rounded">
          {message}
        </div>
      )}

      {/* Current Plan Alert */}
      {user?.plan === "Free" ? (
        <div className="bg-bg-surface border border-border-subtle p-6 flex items-start gap-5">
           <AlertCircle className="h-5 w-5 text-text-subtle shrink-0 mt-0.5" />
           <div>
              <h4 className="font-serif italic text-xl text-text-title mb-2">You are currently on the Free plan.</h4>
              <p className="text-sm tracking-wide text-text-body leading-relaxed border-l-2 border-border-subtle pl-4">
                 You have used {Math.round((jobCount / searchQuotaLimit) * 100)}% of your daily search quota. Upgrade to Pro for full evidence panels and higher limits.
              </p>
           </div>
        </div>
      ) : (
        <div className="bg-bg-surface border border-emerald-500/30 p-6 flex items-start gap-5">
           <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0 mt-0.5" />
           <div>
              <h4 className="font-serif italic text-xl text-text-title mb-2">You are currently on the {user?.plan} plan!</h4>
              <p className="text-sm tracking-wide text-text-body leading-relaxed border-l-2 border-emerald-500/30 pl-4">
                 Thank you for supporting our workspace. You have access to {searchQuotaLimit} searches per day and {monitorLimit} active monitors.
              </p>
           </div>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-8">
         {/* Usage Card */}
         <Card className="bg-bg-surface border-border-subtle">
            <CardHeader className="border-b border-border-subtle pb-6 mb-6">
               <CardTitle className="text-xl font-serif italic text-text-title mb-2">Usage Summary</CardTitle>
               <CardDescription className="text-[10px] font-bold text-text-subtle">Resets daily</CardDescription>
            </CardHeader>
            <CardContent className="space-y-8">
               <div>
                  <div className="flex justify-between text-[10px] uppercase tracking-widest font-bold text-text-subtle mb-3">
                     <span>Deep Searches</span>
                     <span className="font-mono text-text-body">{jobCount} / {searchQuotaLimit}</span>
                  </div>
                  <div className="h-1 w-full bg-border-subtle overflow-hidden">
                     <div 
                       className="h-full bg-amber-600 transition-all duration-500" 
                       style={{ width: `${Math.min(100, (jobCount / searchQuotaLimit) * 100)}%` }}
                     />
                  </div>
               </div>
               <div>
                  <div className="flex justify-between text-[10px] uppercase tracking-widest font-bold text-text-subtle mb-3">
                     <span>Active Monitors</span>
                     <span className="font-mono text-text-body">{monitorsCount} / {monitorLimit}</span>
                  </div>
                  <div className="h-1 w-full bg-border-subtle overflow-hidden">
                     <div 
                       className="h-full bg-border-accent transition-all duration-500" 
                       style={{ width: `${Math.min(100, (monitorsCount / monitorLimit) * 100)}%` }}
                     />
                  </div>
               </div>
            </CardContent>
         </Card>

         {/* Upgrade Card */}
         <Card className="border-border-accent bg-bg-deep relative shadow-2xl">
            <div className="absolute top-0 right-0 bg-accent text-accent-foreground border border-border-accent text-[9px] font-bold px-3 py-1 uppercase tracking-[0.2em] transform translate-x-2 -translate-y-2">
               Recommended
            </div>
            <CardHeader className="border-b border-border-subtle pb-6 mb-6 pt-8">
               <CardTitle className="text-3xl font-serif italic text-text-title mb-4">Pro Plan</CardTitle>
               <CardDescription className="text-sm tracking-wide text-text-subtle">$49/month &bull; Billed monthly</CardDescription>
            </CardHeader>
            <CardContent>
               <ul className="space-y-5">
                  <li className="flex items-start text-xs text-text-body">
                     <CheckCircle2 className="h-4 w-4 text-text-subtle shrink-0 mr-4 mt-0.5" />
                     <span>500 searches/day</span>
                  </li>
                  <li className="flex items-start text-xs text-text-body">
                     <CheckCircle2 className="h-4 w-4 text-text-subtle shrink-0 mr-4 mt-0.5" />
                     <span className="leading-relaxed">10 Active Continuous Monitors</span>
                  </li>
                  <li className="flex items-start text-xs text-text-body">
                     <CheckCircle2 className="h-4 w-4 text-text-subtle shrink-0 mr-4 mt-0.5" />
                     <span>Up to 20 collections</span>
                  </li>
               </ul>
            </CardContent>
            <CardFooter className="pt-8">
               <Button 
                 className="w-full"
                 disabled={user?.plan === "Pro" || upgrading}
                 onClick={() => handleUpgrade("Pro")}
               >
                  {upgrading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  {user?.plan === "Pro" ? "Current Plan" : "Upgrade to Pro"}
               </Button>
            </CardFooter>
         </Card>
      </div>

      {/* Enterprise CTA */}
      <div className="border border-border-subtle p-12 bg-bg-surface text-center">
         <h3 className="text-3xl font-serif italic text-text-title mb-4">Need team collaboration or API access?</h3>
         <p className="text-sm tracking-wide text-text-body leading-relaxed mb-8 max-w-xl mx-auto">Our Team and Enterprise tiers offer shared workspaces, advanced audit logs, SSO, and dedicated success managers.</p>
         <Button 
           variant="outline" 
           disabled={user?.plan === "Enterprise" || upgrading}
           onClick={() => handleUpgrade("Enterprise")}
           className="border-border-subtle hover:border-border-accent text-text-body hover:bg-bg-panel hover:text-text-title bg-bg-surface"
         >
            {user?.plan === "Enterprise" ? "Active Enterprise Plan" : "Upgrade to Enterprise"}
         </Button>
      </div>
    </div>
  );
}
