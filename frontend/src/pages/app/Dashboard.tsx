import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Activity, Search, Database, ArrowRight, Loader2, CreditCard } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { api, JobResponse } from "@/lib/api";
import { withWakeupRetry } from "@/lib/retry";

type DashboardUser = {
  plan?: string;
  search_used?: number;
  search_quota_limit?: number;
};

function SkeletonCard() {
  return (
    <div className="rounded-2xl bg-background-surface border border-border-subtle p-6 space-y-4 animate-pulse shadow-card">
      <div className="flex justify-between items-center">
        <div className="h-3.5 bg-background-panel w-2/3 rounded-md"></div>
        <div className="h-4 w-4 bg-background-panel rounded-md"></div>
      </div>
      <div className="h-8 bg-background-panel w-1/3 rounded-md"></div>
      <div className="h-3 bg-background-panel w-1/2 rounded-md"></div>
    </div>
  );
}

function SkeletonActivity() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((n) => (
        <div key={n} className="p-4 rounded-xl bg-background-deep border border-border-subtle space-y-3 animate-pulse">
          <div className="flex justify-between">
            <div className="h-4 bg-background-panel w-2/3 rounded-md"></div>
            <div className="h-3 bg-background-panel w-12 rounded-md"></div>
          </div>
          <div className="h-3 bg-background-panel w-20 rounded-md"></div>
        </div>
      ))}
    </div>
  );
}

export function Dashboard() {
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [monitorsCount, setMonitorsCount] = useState<number>(0);
  const [user, setUser] = useState<DashboardUser | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const [userData, jobsData, monitorsData] = await Promise.all([
        withWakeupRetry(() => api.getCurrentUser()),
        withWakeupRetry(() => api.getJobs(6)),
        withWakeupRetry(() => api.getMonitors()),
      ]);
      setUser(userData as DashboardUser);
      setJobs(jobsData);
      setMonitorsCount(monitorsData.length);
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
      setLoadError("Could not load dashboard. The API may be waking up — try Sync Stats.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const completedJobs = jobs.filter((j) => j.status === "completed").length;
  const searchUsed = user?.search_used ?? 0;
  const searchQuota = user?.search_quota_limit ?? 50;
  const planName = user?.plan ?? "Free";

  return (
    <div className="space-y-8 select-none">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-text-title">Civic Intelligence Overview</h2>
          <p className="text-text-subtle mt-1 text-xs font-medium">
            Workspace activity, verified evidence records, and research quota.
          </p>
        </div>
        <Button onClick={fetchDashboardData} size="sm" variant="outline" className="h-9 self-start sm:self-auto">
          {isLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" /> : null} Sync Stats
        </Button>
      </div>

      {/* Public Social Impact Quick Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border border-primary/20 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-xs">
        <div className="space-y-1.5 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-primary/15 text-primary text-[11px] font-semibold">
            <span>Credence 2.0 Engine</span>
            <span>•</span>
            <span>Public Trust Architecture</span>
          </div>
          <h3 className="text-lg font-bold text-text-title tracking-tight">
            Public Social Impact & Evidence Verification Workspace
          </h3>
          <p className="text-xs text-text-body/80 leading-relaxed">
            Investigate public health claims, civic spending, climate metrics, and governance policies with 8-gate verification, zero probability theater, and 100% frozen citations.
          </p>
        </div>
        <Button asChild size="default" className="shrink-0 bg-primary text-primary-foreground font-semibold text-xs shadow-md">
          <Link to="/app/research">Launch Research Studio <ArrowRight className="h-3.5 w-3.5 ml-2" /></Link>
        </Button>
      </div>

      {loadError && (
        <div className="p-4 bg-amber-500/10 border-l-4 border-amber-500 text-amber-500 text-xs font-semibold rounded-xl">
          {loadError}
        </div>
      )}

      {/* Overview Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {isLoading ? (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        ) : (
          <>
            <Card className="flex flex-col justify-between p-6 space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-border-subtle/10">
                  <span className="text-xs font-semibold text-text-subtle">Research Jobs Used</span>
                  <Search className="h-4 w-4 text-primary" />
                </div>
                <div className="text-3xl font-bold tracking-tight text-text-title font-sans">
                  {searchUsed} / {searchQuota}
                </div>
                <p className="text-xs text-text-subtle mt-1 font-medium">
                  {completedJobs} completed in recent list
                </p>
              </div>
              <Button asChild size="sm" variant="outline" className="w-full h-9">
                <Link to="/app/search">Run Goal Plan <ArrowRight className="h-3.5 w-3.5 ml-1.5" /></Link>
              </Button>
            </Card>

            <Card className="flex flex-col justify-between p-6 space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-border-subtle/10">
                  <span className="text-xs font-semibold text-text-subtle">Recent Jobs</span>
                  <Activity className="h-4 w-4 text-primary" />
                </div>
                <div className="text-3xl font-bold tracking-tight text-text-title font-sans">{jobs.length}</div>
                <p className="text-xs text-text-subtle mt-1 font-medium">
                  Last 6 research jobs
                </p>
              </div>
              <Button asChild size="sm" variant="outline" className="w-full h-9">
                <Link to="/app/search">View Search <ArrowRight className="h-3.5 w-3.5 ml-1.5" /></Link>
              </Button>
            </Card>

            <Card className="flex flex-col justify-between p-6 space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-border-subtle/10">
                  <span className="text-xs font-semibold text-text-subtle">Active Monitors</span>
                  <Database className="h-4 w-4 text-primary" />
                </div>
                <div className="text-3xl font-bold tracking-tight text-text-title font-sans">{monitorsCount}</div>
                <p className="text-xs text-text-subtle mt-1 font-medium">
                  Manual check on free tier
                </p>
              </div>
              <Button asChild size="sm" variant="outline" className="w-full h-9">
                <Link to="/app/monitors">Manage Monitors <ArrowRight className="h-3.5 w-3.5 ml-1.5" /></Link>
              </Button>
            </Card>

            <Card className="flex flex-col justify-between p-6 space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-border-subtle/10">
                  <span className="text-xs font-semibold text-text-subtle">Account Plan</span>
                  <CreditCard className="h-4 w-4 text-primary" />
                </div>
                <div className="text-3xl font-bold tracking-tight text-text-title font-sans">{planName}</div>
                <p className="text-xs text-text-subtle mt-1 font-medium">
                  {searchQuota} research jobs / day
                </p>
              </div>
              <Button asChild size="sm" variant="outline" className="w-full h-9">
                <Link to="/app/billing">View Billing <ArrowRight className="h-3.5 w-3.5 ml-1.5" /></Link>
              </Button>
            </Card>
          </>
        )}
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7 pt-2">
        <Card className="col-span-4 p-6">
          <CardHeader className="border-b border-border-subtle/10 pb-6 mb-6">
            <CardTitle className="text-lg font-bold tracking-tight text-text-title mb-1">Recent Activity</CardTitle>
            <CardDescription className="text-text-subtle">Your latest research jobs.</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <SkeletonActivity />
            ) : jobs.length === 0 ? (
              <div className="p-8 border border-dashed border-border-subtle/20 text-center rounded-2xl bg-bg-panel/10">
                <p className="text-sm text-text-subtle font-medium">No research jobs yet.</p>
                <p className="text-xs text-text-subtle mt-2 font-medium">
                  Run an AI Agent Goal Plan from Search to get started.
                </p>
                <Button asChild size="sm" variant="outline" className="mt-4">
                  <Link to="/app/search">Go to Search</Link>
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {jobs.map((job) => (
                  <div key={job.job_id} className="flex flex-col gap-3 p-4 rounded-xl bg-background-deep border border-border-subtle hover:border-border-accent/40 transition-all duration-200">
                    <div className="flex items-start justify-between gap-4">
                      <div className="font-semibold text-sm text-text-body leading-relaxed font-sans">{job.input}</div>
                      <span className="text-[10px] font-mono whitespace-nowrap text-text-subtle uppercase tracking-wider mt-1">
                        {new Date(job.submitted_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs font-semibold text-text-subtle">
                      <span className="border border-border-subtle/20 bg-bg-panel/40 px-2 py-0.5 rounded-lg text-text-body font-sans">
                        {job.results_count} Results
                      </span>
                      <span className={`flex items-center ${
                        job.status === "completed" ? "text-highlight-color" : "text-amber-500"
                      }`}>
                        <span className={`w-2 h-2 rounded-full mr-2 ${
                          job.status === "completed" ? "bg-highlight-color" : "bg-amber-500 animate-[pulse_2s_infinite]"
                        }`}></span>
                        {job.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="col-span-3 p-6">
          <CardHeader className="border-b border-border-subtle/10 pb-6 mb-6">
            <CardTitle className="text-lg font-bold tracking-tight text-text-title mb-1">Getting Started</CardTitle>
            <CardDescription className="text-text-subtle font-medium">Free-tier workflow tips.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5 text-sm text-text-body leading-relaxed">
            <p className="border-l-2 border-primary pl-3 bg-bg-panel/10 py-1 pr-1 rounded-r-lg">
              Use <strong className="font-semibold text-text-title">AI Agent Goal Plan</strong> first to crawl sources and populate your index.
            </p>
            <p className="border-l-2 border-border-subtle/40 pl-3 bg-bg-panel/10 py-1 pr-1 rounded-r-lg">
              After jobs complete, <strong className="font-semibold text-text-title">Standard Search</strong> queries your indexed documents.
            </p>
            <p className="border-l-2 border-border-subtle/40 pl-3 text-text-subtle text-xs font-medium bg-bg-panel/10 py-1 pr-1 rounded-r-lg">
              First API request after idle may take 30–60s while Render wakes up.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
