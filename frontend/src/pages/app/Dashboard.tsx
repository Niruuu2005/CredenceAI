import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Activity, ArrowUpRight, Search, Users, Database, ArrowRight, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { api, JobResponse } from "@/lib/api";

export function Dashboard() {
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [monitorsCount, setMonitorsCount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(false);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      const jobsData = await api.getJobs(6);
      setJobs(jobsData);
      
      const monitorsData = await api.getMonitors();
      setMonitorsCount(monitorsData.length);
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const totalCompletedSearches = jobs.filter(j => j.status === "completed").length;

  return (
    <div className="h-full overflow-y-auto pr-2 space-y-8 bg-bg-deep text-text-body">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-serif italic text-text-title font-medium">Overview</h2>
          <p className="text-text-subtle mt-2 text-xs uppercase tracking-widest font-medium">Here's what's happening in your workspace today.</p>
        </div>
        <Button onClick={fetchDashboardData} size="sm" variant="outline" className="border-border-subtle bg-bg-surface text-[10px] uppercase font-semibold h-9 tracking-wider">
          {isLoading ? <Loader2 className="h-3 w-3 animate-spin mr-1.5" /> : null} Sync Stats
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-bg-surface border-border-subtle flex flex-col justify-between">
          <div>
            <CardHeader className="flex flex-row items-center justify-between pb-4 border-b border-border-subtle">
              <CardTitle className="text-[10px] uppercase tracking-widest font-medium text-text-subtle">Total Searches</CardTitle>
              <Search className="h-4 w-4 text-text-subtle" />
            </CardHeader>
            <CardContent className="pt-6">
              <div className="text-4xl font-serif italic text-text-title">
                {1248 + totalCompletedSearches}
              </div>
              <p className="text-[10px] uppercase tracking-widest font-medium text-text-subtle mt-3">+{totalCompletedSearches} this session</p>
            </CardContent>
          </div>
          <div className="p-6 pt-0 mt-2 border-t border-border-subtle">
            <Button asChild size="sm" variant="outline" className="w-full border-border-subtle bg-bg-deep text-[10px] uppercase tracking-wider font-semibold h-9 hover:bg-bg-panel hover:text-text-title text-text-body">
              <Link to="/app/search">Run New Search <ArrowRight className="h-3 w-3 ml-1.5" /></Link>
            </Button>
          </div>
        </Card>

        <Card className="bg-bg-surface border-border-subtle flex flex-col justify-between">
          <div>
            <CardHeader className="flex flex-row items-center justify-between pb-4 border-b border-border-subtle">
              <CardTitle className="text-[10px] uppercase tracking-widest font-medium text-text-subtle">Entities Tracked</CardTitle>
              <Activity className="h-4 w-4 text-text-subtle" />
            </CardHeader>
            <CardContent className="pt-6">
              <div className="text-4xl font-serif italic text-text-title">
                {145 + (totalCompletedSearches * 2)}
              </div>
              <p className="text-[10px] uppercase tracking-widest font-medium text-text-subtle mt-3">+{totalCompletedSearches * 2} this session</p>
            </CardContent>
          </div>
          <div className="p-6 pt-0 mt-2 border-t border-border-subtle">
            <Button asChild size="sm" variant="outline" className="w-full border-border-subtle bg-bg-deep text-[10px] uppercase tracking-wider font-semibold h-9 hover:bg-bg-panel hover:text-text-title text-text-body">
              <Link to="/app/collections">Open Collections <ArrowRight className="h-3 w-3 ml-1.5" /></Link>
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
              <div className="flex items-center text-[10px] uppercase tracking-widest font-bold text-highlight-color mt-3">
                 <span className="w-1.5 h-1.5 bg-highlight-color mr-2 animate-pulse"></span>
                 All running smoothly
              </div>
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
              <CardTitle className="text-[10px] uppercase tracking-widest font-medium text-text-subtle">Team Admin</CardTitle>
              <Users className="h-4 w-4 text-text-subtle" />
            </CardHeader>
            <CardContent className="pt-6">
              <div className="text-4xl font-serif italic text-text-title font-medium">5 Users</div>
              <p className="text-[10px] uppercase tracking-widest font-medium text-text-subtle mt-3">Free Tier Limit reached</p>
            </CardContent>
          </div>
          <div className="p-6 pt-0 mt-2 border-t border-border-subtle">
            <Button asChild size="sm" variant="outline" className="w-full border-border-subtle bg-bg-deep text-[10px] uppercase tracking-wider font-semibold h-9 hover:bg-bg-panel hover:text-text-title text-text-body">
              <Link to="/app/billing">Upgrade Seats <ArrowRight className="h-3 w-3 ml-1.5" /></Link>
            </Button>
          </div>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4 bg-bg-surface border-border-subtle">
          <CardHeader className="border-b border-border-subtle pb-6 mb-6">
            <CardTitle className="text-xl font-serif italic text-text-title mb-2">Recent Activity</CardTitle>
            <CardDescription className="text-text-subtle">Your latest searches and entity updates.</CardDescription>
          </CardHeader>
          <CardContent>
             <div className="space-y-4">
                {jobs.length === 0 ? (
                  // Default mock items if no searches are run yet
                  [1,2,3,4].map((i) => (
                     <div key={i} className="flex flex-col gap-3 p-5 border border-border-subtle hover:border-border-accent bg-bg-deep transition-colors rounded-sm">
                        <div className="flex items-start justify-between gap-4">
                           <div className="font-medium text-sm text-text-body leading-relaxed font-serif italic">Taiwanese semiconductor supply chains and wafer telemetry updates.</div>
                           <div className="text-[10px] font-mono whitespace-nowrap text-text-subtle uppercase tracking-widest mt-1">Archive</div>
                        </div>
                        <div className="flex items-center gap-4 text-[10px] uppercase tracking-widest font-bold text-text-subtle">
                           <span className="border border-border-subtle bg-bg-panel px-2 py-1 text-text-body font-sans">42 Results</span>
                           <span className="flex items-center text-highlight-color"><span className="w-1.5 h-1.5 bg-highlight-color mr-2"></span> High Confidence</span>
                        </div>
                     </div>
                  ))
                ) : (
                  jobs.map((job) => (
                    <div key={job.job_id} className="flex flex-col gap-3 p-5 border border-border-subtle hover:border-border-accent bg-bg-deep transition-colors rounded-sm">
                       <div className="flex items-start justify-between gap-4">
                          <div className="font-medium text-sm text-text-body leading-relaxed font-sans">{job.input}</div>
                          <span className="text-[10px] font-mono whitespace-nowrap text-text-subtle uppercase tracking-widest mt-1">
                            {new Date(job.submitted_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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
            <CardTitle className="text-xl font-serif italic text-text-title mb-2">Critical Alerts</CardTitle>
            <CardDescription className="text-text-subtle">Monitors that require your attention.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
               <div className="p-5 border border-amber-500 bg-bg-deep rounded-sm">
                  <div className="font-serif italic text-amber-600 text-lg mb-2">Entity Flag: "Global Logistics Corp"</div>
                  <div className="text-text-body text-sm mb-4 leading-relaxed border-l-2 border-amber-500 pl-3">New regulatory filing detected indicating potential merger conflict.</div>
                  <Link to="#" className="text-[10px] font-bold uppercase tracking-widest text-amber-600 hover:text-amber-500 transition-colors flex items-center">View Details <ArrowUpRight className="h-3 w-3 ml-1"/></Link>
               </div>
               <div className="p-5 border border-border-subtle bg-bg-deep rounded-sm">
                  <div className="font-serif italic text-text-body text-lg mb-2">Source Health Warning</div>
                  <div className="text-text-subtle text-sm leading-relaxed border-l-2 border-border-subtle pl-3">Primary API for European Patent Database is experiencing rate limiting.</div>
               </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
