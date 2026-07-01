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
    <div className="h-full overflow-y-auto pr-2 space-y-8 bg-bg-deep text-text-body">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-serif italic text-text-title font-medium">Overview</h2>
          <p className="text-text-subtle mt-2 text-xs uppercase tracking-widest font-medium">
            Your workspace activity and research job quota.
          </p>
        </div>
        <Button onClick={fetchDashboardData} size="sm" variant="outline" className="border-border-subtle bg-bg-surface text-[10px] uppercase font-semibold h-9 tracking-wider">
          {isLoading ? <Loader2 className="h-3 w-3 animate-spin mr-1.5" /> : null} Sync Stats
        </Button>
      </div>

      {loadError && (
        <div className="p-4 border border-amber-500/30 bg-amber-950/20 text-amber-500 text-xs uppercase tracking-wide">
          {loadError}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-bg-surface border-border-subtle flex flex-col justify-between">
          <div>
            <CardHeader className="flex flex-row items-center justify-between pb-4 border-b border-border-subtle">
              <CardTitle className="text-[10px] uppercase tracking-widest font-medium text-text-subtle">Research Jobs Used</CardTitle>
              <Search className="h-4 w-4 text-text-subtle" />
            </CardHeader>
            <CardContent className="pt-6">
              <div className="text-4xl font-serif italic text-text-title">
                {searchUsed} / {searchQuota}
              </div>
              <p className="text-[10px] uppercase tracking-widest font-medium text-text-subtle mt-3">
                {completedJobs} completed in recent list
              </p>
            </CardContent>
          </div>
          <div className="p-6 pt-0 mt-2 border-t border-border-subtle">
            <Button asChild size="sm" variant="outline" className="w-full border-border-subtle bg-bg-deep text-[10px] uppercase tracking-wider font-semibold h-9 hover:bg-bg-panel hover:text-text-title text-text-body">
              <Link to="/app/search">Run Goal Plan <ArrowRight className="h-3 w-3 ml-1.5" /></Link>
            </Button>
          </div>
        </Card>

        <Card className="bg-bg-surface border-border-subtle flex flex-col justify-between">
          <div>
            <CardHeader className="flex flex-row items-center justify-between pb-4 border-b border-border-subtle">
              <CardTitle className="text-[10px] uppercase tracking-widest font-medium text-text-subtle">Recent Jobs</CardTitle>
              <Activity className="h-4 w-4 text-text-subtle" />
            </CardHeader>
            <CardContent className="pt-6">
              <div className="text-4xl font-serif italic text-text-title">{jobs.length}</div>
              <p className="text-[10px] uppercase tracking-widest font-medium text-text-subtle mt-3">
                Last 6 research jobs
              </p>
            </CardContent>
          </div>
          <div className="p-6 pt-0 mt-2 border-t border-border-subtle">
            <Button asChild size="sm" variant="outline" className="w-full border-border-subtle bg-bg-deep text-[10px] uppercase tracking-wider font-semibold h-9 hover:bg-bg-panel hover:text-text-title text-text-body">
              <Link to="/app/search">View Search <ArrowRight className="h-3 w-3 ml-1.5" /></Link>
            </Button>
          </div>
        </Card>

        <Card className="bg-bg-surface border-border-subtle flex flex-col justify-between">
          <div>
            <CardHeader className="flex flex-row items-center justify-between pb-4 border-b border-border-subtle">
              <CardTitle className="text-[10px] uppercase tracking-widest font-medium text-text-subtle">Active Monitors</CardTitle>
              <Database className="h-4 w-4 text-text-subtle" />
            </CardHeader>
            <CardContent className="pt-6">
              <div className="text-4xl font-serif italic text-text-title">{monitorsCount}</div>
              <p className="text-[10px] uppercase tracking-widest font-medium text-text-subtle mt-3">
                Manual check on free tier
              </p>
            </CardContent>
          </div>
          <div className="p-6 pt-0 mt-2 border-t border-border-subtle">
            <Button asChild size="sm" variant="outline" className="w-full border-border-subtle bg-bg-deep text-[10px] uppercase tracking-wider font-semibold h-9 hover:bg-bg-panel hover:text-text-title text-text-body">
              <Link to="/app/monitors">Manage Monitors <ArrowRight className="h-3 w-3 ml-1.5" /></Link>
            </Button>
          </div>
        </Card>

        <Card className="bg-bg-surface border-border-subtle flex flex-col justify-between">
          <div>
            <CardHeader className="flex flex-row items-center justify-between pb-4 border-b border-border-subtle">
              <CardTitle className="text-[10px] uppercase tracking-widest font-medium text-text-subtle">Account Plan</CardTitle>
              <CreditCard className="h-4 w-4 text-text-subtle" />
            </CardHeader>
            <CardContent className="pt-6">
              <div className="text-4xl font-serif italic text-text-title font-medium">{planName}</div>
              <p className="text-[10px] uppercase tracking-widest font-medium text-text-subtle mt-3">
                {searchQuota} research jobs / day
              </p>
            </CardContent>
          </div>
          <div className="p-6 pt-0 mt-2 border-t border-border-subtle">
            <Button asChild size="sm" variant="outline" className="w-full border-border-subtle bg-bg-deep text-[10px] uppercase tracking-wider font-semibold h-9 hover:bg-bg-panel hover:text-text-title text-text-body">
              <Link to="/app/billing">View Billing <ArrowRight className="h-3 w-3 ml-1.5" /></Link>
            </Button>
          </div>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4 bg-bg-surface border-border-subtle">
          <CardHeader className="border-b border-border-subtle pb-6 mb-6">
            <CardTitle className="text-xl font-serif italic text-text-title mb-2">Recent Activity</CardTitle>
            <CardDescription className="text-text-subtle">Your latest research jobs.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {jobs.length === 0 ? (
                <div className="p-8 border border-dashed border-border-subtle text-center rounded-sm">
                  <p className="text-sm text-text-subtle font-serif italic">No research jobs yet.</p>
                  <p className="text-[10px] uppercase tracking-widest text-text-subtle mt-2">
                    Run an AI Agent Goal Plan from Search to get started.
                  </p>
                  <Button asChild size="sm" variant="outline" className="mt-4 border-border-subtle">
                    <Link to="/app/search">Go to Search</Link>
                  </Button>
                </div>
              ) : (
                jobs.map((job) => (
                  <div key={job.job_id} className="flex flex-col gap-3 p-5 border border-border-subtle hover:border-border-accent bg-bg-deep transition-colors rounded-sm">
                    <div className="flex items-start justify-between gap-4">
                      <div className="font-medium text-sm text-text-body leading-relaxed font-sans">{job.input}</div>
                      <span className="text-[10px] font-mono whitespace-nowrap text-text-subtle uppercase tracking-widest mt-1">
                        {new Date(job.submitted_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-[10px] uppercase tracking-widest font-bold text-text-subtle">
                      <span className="border border-border-subtle bg-bg-panel px-2 py-1 text-text-body">
                        {job.results_count} Results
                      </span>
                      <span className={`flex items-center ${
                        job.status === "completed" ? "text-highlight-color" : "text-amber-500"
                      }`}>
                        <span className={`w-1.5 h-1.5 mr-2 ${
                          job.status === "completed" ? "bg-highlight-color" : "bg-amber-500 animate-pulse"
                        }`}></span>
                        {job.status}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
        <Card className="col-span-3 bg-bg-surface border-border-subtle">
          <CardHeader className="border-b border-border-subtle pb-6 mb-6">
            <CardTitle className="text-xl font-serif italic text-text-title mb-2">Getting Started</CardTitle>
            <CardDescription className="text-text-subtle">Free-tier workflow tips.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-text-body leading-relaxed">
            <p className="border-l-2 border-highlight-color pl-3">
              Use <strong className="font-normal text-text-title">AI Agent Goal Plan</strong> first to crawl sources and populate your index.
            </p>
            <p className="border-l-2 border-border-subtle pl-3">
              After jobs complete, <strong className="font-normal text-text-title">Standard Search</strong> queries your indexed documents.
            </p>
            <p className="border-l-2 border-border-subtle pl-3 text-text-subtle text-xs uppercase tracking-wider">
              First API request after idle may take 30–60s while Render wakes up.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
