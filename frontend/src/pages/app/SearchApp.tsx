import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { 
  Search, Database, ShieldCheck, ShieldAlert, 
  FileText, Download, Loader2, CheckCircle2, 
  XCircle, ArrowRight, Activity 
} from "lucide-react";
import { api, SearchDocument, JobResponse, JobNormalizedResult } from "@/lib/api";
import { withWakeupRetry } from "@/lib/retry";

function formatApiError(err: unknown, fallback: string): string {
  const e = err as {
    message?: string;
    traceId?: string;
    details?: { trace_id?: string };
  };
  const base = e?.message || fallback;
  const traceId = e?.traceId || e?.details?.trace_id;
  return traceId ? `${base} (trace: ${traceId})` : base;
}

type ExtractedEntity = { name: string; type?: string; confidence: number };

function deriveSource(url: string, source?: string): string {
  if (source?.trim()) return source.trim();
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "web";
  }
}

function mapNormalizedResultToDocument(r: JobNormalizedResult): SearchDocument {
  const score = r.quality_scores?.final_trust_score ?? 0.85;
  return {
    document_id: r.id,
    job_id: r.job_id,
    url: r.url,
    title: r.title,
    main_text: r.snippet || "",
    description: r.snippet || "",
    language: "en",
    content_type: "web",
    source: deriveSource(r.url, r.source),
    source_type: "web",
    quality_score: score,
    extraction_quality_score: score,
    trusted: r.quality_scores?.decision === "accept" || score > 0.8,
    indexed_at: null,
    created_at: null,
  };
}

function collectEntities(results: JobNormalizedResult[]): ExtractedEntity[] {
  const seen = new Map<string, ExtractedEntity>();
  for (const r of results) {
    for (const e of r.entities ?? []) {
      const key = e.canonical_name.toLowerCase();
      const existing = seen.get(key);
      if (!existing || e.confidence > existing.confidence) {
        seen.set(key, {
          name: e.canonical_name,
          type: e.entity_type ?? undefined,
          confidence: e.confidence,
        });
      }
    }
  }
  return Array.from(seen.values()).sort((a, b) => b.confidence - a.confidence);
}

function isJobPending(job: JobResponse): boolean {
  return job.status === "submitted" || job.status === "processing";
}

export function SearchApp() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<"search" | "goal">("search");
  const [hasSearched, setHasSearched] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Search Results State
  const [searchResults, setSearchResults] = useState<SearchDocument[]>([]);
  const [totalResults, setTotalResults] = useState(0);
  const [extractedEntities, setExtractedEntities] = useState<ExtractedEntity[]>([]);

  // Goal Plan State
  const [activeGoal, setActiveGoal] = useState<{ planId: string; goal: string } | null>(null);
  const [pollingJobs, setPollingJobs] = useState<JobResponse[]>([]);
  const [agentDecisions, setAgentDecisions] = useState<Array<{ agent_name: string; reasoning: string; success: boolean }>>([]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    if (mode === "search") {
      setActiveGoal(null);
      setPollingJobs([]);
      setExtractedEntities([]);
      performSearch(query);
    } else {
      setSearchResults([]);
      setTotalResults(0);
      setExtractedEntities([]);
      handleGoalSubmit(query);
    }
  };

  const performSearch = async (q: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await withWakeupRetry(() => api.search(q));
      setSearchResults(
        res.results.map((r) => ({
          ...r.document,
          source: deriveSource(r.document.url, r.document.source),
        }))
      );
      setTotalResults(res.total);
      setExtractedEntities([]);
      setHasSearched(true);
    } catch (err: unknown) {
      setError(formatApiError(err, "Failed to fetch search results"));
    } finally {
      setIsLoading(false);
    }
  };

  const loadGoalResults = async (jobs: JobResponse[], goalText: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const completed = jobs.filter((j) => j.status === "completed");
      const allResults: JobNormalizedResult[] = [];

      for (const job of completed) {
        const embedded = job.result?.results;
        if (Array.isArray(embedded) && embedded.length > 0) {
          allResults.push(...embedded);
        } else if (job.results_count > 0) {
          const results = await api.getJobResults(job.job_id);
          allResults.push(...results);
        }
      }

      if (allResults.length > 0) {
        const docs = allResults.map(mapNormalizedResultToDocument);
        setSearchResults(docs);
        setTotalResults(docs.length);
        setExtractedEntities(collectEntities(allResults));
        const firstJobId = completed[0]?.job_id;
        if (firstJobId) {
          try {
            const decisions = await api.getAgentDecisions(firstJobId);
            setAgentDecisions(decisions);
          } catch {
            setAgentDecisions([]);
          }
        }
        return;
      }

      const res = await withWakeupRetry(() => api.search(goalText));
      setSearchResults(
        res.results.map((r) => ({
          ...r.document,
          source: deriveSource(r.document.url, r.document.source),
        }))
      );
      setTotalResults(res.total);
      setExtractedEntities([]);
    } catch (err: unknown) {
      setError(formatApiError(err, "Failed to load research results"));
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoalSubmit = async (q: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await withWakeupRetry(() => api.submitGoal(q));
      setActiveGoal({
        planId: res.plan_id,
        goal: res.goal,
      });
      setPollingJobs(res.jobs);
      setHasSearched(true);
      const allDone = res.jobs.every(
        (j) => j.status === "completed" || j.status === "failed"
      );
      if (allDone) {
        const failed = res.jobs.find((j) => j.status === "failed");
        if (failed) {
          setError(
            failed.error_message
              ? `Research job failed: ${failed.error_message}`
              : "Research job failed. Try a simpler query."
          );
        } else if (res.jobs.some((j) => j.status === "completed")) {
          await loadGoalResults(res.jobs, res.goal);
        }
      }
    } catch (err: unknown) {
      setError(formatApiError(err, "Failed to submit goal plan"));
    } finally {
      setIsLoading(false);
    }
  };

  // Poll for background jobs generated by Goal submission
  useEffect(() => {
    if (pollingJobs.length === 0) return;
    
    const hasPending = pollingJobs.some(isJobPending);

    const anyFailed = pollingJobs.some((job) => job.status === "failed");

    if (!hasPending) {
      if (anyFailed) {
        const failed = pollingJobs.find((j) => j.status === "failed");
        setError(
          failed?.error_message
            ? `Research job failed: ${failed.error_message}`
            : "Research job failed. Check Render logs or try a simpler query."
        );
        return;
      }
      if (activeGoal) {
        loadGoalResults(pollingJobs, activeGoal.goal);
      }
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const updatedJobs = await Promise.all(
          pollingJobs.map(async (job) => {
            if (isJobPending(job)) {
              return await withWakeupRetry(() => api.getJob(job.job_id));
            }
            return job;
          })
        );
        setPollingJobs(updatedJobs);
      } catch (err) {
        console.error("Error polling jobs:", err);
      }
    }, 2000);

    return () => clearTimeout(timer);
  }, [pollingJobs, activeGoal]);

  // Client-side CSV exporter
  const handleExportCSV = () => {
    if (searchResults.length === 0) return;
    
    // Headers
    const headers = ["Title", "URL", "Snippet", "Source", "Quality Score", "Trusted"];
    
    // Rows
    const rows = searchResults.map(r => [
      r.title || "",
      r.url || "",
      r.main_text || r.description || "",
      r.source || "",
      r.quality_score ? (r.quality_score * 100).toFixed(0) : "100",
      r.trusted ? "true" : "false"
    ]);
    
    // CSV content formatting
    const csvContent = [
      headers.join(","),
      ...rows.map(row => row.map(val => `"${val.replace(/"/g, '""')}"`).join(","))
    ].join("\n");
    
    // Download trigger
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `credenceai_search_${Date.now()}.csv`);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const uniqueSources = Array.from(
    new Set(searchResults.map((r) => deriveSource(r.url, r.source)).filter(Boolean))
  );

  const jobsStillRunning =
    activeGoal && pollingJobs.some(isJobPending);
  
  // Calculate aggregate stats for standard results
  const avgTrustScore = searchResults.length > 0 
    ? Math.round(searchResults.reduce((acc, curr) => acc + (curr.quality_score * 100), 0) / searchResults.length)
    : 0;

  return (
    <div className="h-full flex flex-col bg-bg-deep text-text-body">
      <div className="mb-8 max-w-3xl">
        <h2 className="text-3xl font-serif italic text-text-title mb-2">Deep Search & Intelligence</h2>
        <p className="text-xs text-text-subtle uppercase tracking-wider mb-6">
          Query standard indexes or launch automated AI research goals.
        </p>

        {/* Mode Selector Tabs */}
        <div className="inline-flex p-1.5 rounded-2xl bg-bg-panel/40 neu-inset-sm mb-8">
          <button 
            type="button"
            className={cn(
              "px-5 py-2.5 rounded-xl text-xs uppercase tracking-wider font-bold transition-all cursor-pointer",
              mode === "search" 
                ? "bg-primary text-primary-foreground shadow-sm" 
                : "text-text-subtle hover:text-text-title"
            )}
            onClick={() => {
              setMode("search");
              setHasSearched(false);
              setError(null);
            }}
          >
            Standard Search
          </button>
          <button 
            type="button"
            className={cn(
              "px-5 py-2.5 rounded-xl text-xs uppercase tracking-wider font-bold transition-all cursor-pointer",
              mode === "goal" 
                ? "bg-primary text-primary-foreground shadow-sm" 
                : "text-text-subtle hover:text-text-title"
            )}
            onClick={() => {
              setMode("goal");
              setHasSearched(false);
              setError(null);
            }}
          >
            AI Agent Goal Plan
          </button>
        </div>

        <form onSubmit={handleSearch} className="flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-primary" />
            <Input 
              type="text" 
              className="pl-12"
              placeholder={
                mode === "search" 
                  ? "Query subjects, specific claims, or search keywords..." 
                  : "State research goal (e.g. 'Decompose wafer export changes')..."
              }
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <Button type="submit" className="px-8 whitespace-nowrap" disabled={isLoading}>
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : mode === "search" ? (
              "Search"
            ) : (
              "Plan Goal"
            )}
          </Button>
        </form>

        {error && (
          <div className="mt-4 p-3 bg-red-500/10 border-l-4 border-red-500 text-red-500 text-xs font-semibold rounded-xl">
            {error}
          </div>
        )}
      </div>

      {!hasSearched ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center pb-20 opacity-70">
          <Database className="h-10 w-10 text-text-subtle mb-6" />
          <h3 className="text-xl font-serif italic text-text-title">Ready for your query</h3>
          <p className="text-xs text-text-subtle max-w-sm mt-3 uppercase tracking-wide leading-relaxed">
            {mode === "search" 
              ? "Search indexed semiconductor metrics, public policies, arXiv papers, and corporate registries."
              : "AI agent will review inputs, design a crawl/research plan, schedule jobs, and compile intelligence reports."}
          </p>
        </div>
      ) : (
        <div className="flex-1 flex gap-6 overflow-hidden min-h-0">
          
          {/* Main Content Area */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-2 pb-8">
            
            {/* Goal Progress Sub-panel */}
            {activeGoal && pollingJobs.length > 0 && (
              <div className="p-6 bg-bg-panel/20 neu-inset-sm mb-6 rounded-2xl border-none">
                <div className="flex items-center justify-between mb-4 pb-2 border-b border-border-subtle/10">
                  <div>
                    <span className="text-[9px] uppercase tracking-widest font-bold text-highlight-color">Active Research Goal Plan</span>
                    <h3 className="text-lg font-serif italic text-text-title mt-1">"{activeGoal.goal}"</h3>
                  </div>
                  <span className="text-[10px] font-mono uppercase bg-bg-deep px-2.5 py-1 text-text-subtle border border-border-subtle/20 rounded-xl">
                    Plan ID: {activeGoal.planId.slice(0, 8)}...
                  </span>
                </div>

                <div className="space-y-3">
                  {pollingJobs.map((job, idx) => (
                    <div key={job.job_id} className="flex items-center justify-between p-3.5 bg-bg-deep neu-outset-sm rounded-xl text-xs border-none">
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-text-subtle text-[10px] w-4">{idx + 1}.</span>
                        <div className="flex flex-col">
                          <span className="font-semibold text-text-title capitalize">{job.job_type.replace('_', ' ')}</span>
                          <span className="text-[10px] text-text-subtle mt-0.5 font-mono">{job.input}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {job.status === "completed" && <CheckCircle2 className="h-4 w-4 text-highlight-color" />}
                        {job.status === "failed" && <XCircle className="h-4 w-4 text-red-500" />}
                        {(job.status === "submitted" || job.status === "processing") && (
                          <Loader2 className="h-3.5 w-3.5 text-primary animate-spin" />
                        )}
                        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-xl border ${
                          job.status === "completed" ? "text-highlight-color border-highlight-color/20 bg-highlight-color/10" :
                          job.status === "failed" ? "text-red-500 border-red-500/20 bg-red-500/10" :
                          "text-amber-500 border-amber-500/20 bg-amber-500/10 animate-[pulse_2s_infinite]"
                        }`}>
                          {job.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                {pollingJobs.some(isJobPending) ? (
                  <p className="text-[10px] text-text-subtle uppercase tracking-widest font-semibold mt-4 flex items-center gap-2">
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" /> Research pipeline running — fetching sources and entities.
                  </p>
                ) : (
                  <div className="mt-4 p-3 bg-highlight-color/5 border border-highlight-color/20 text-highlight-color text-[10px] uppercase tracking-wider font-bold rounded-xl flex items-center justify-between">
                    <span>Topic ingestion complete! Loading research results...</span>
                    <Activity className="h-4 w-4 animate-pulse" />
                  </div>
                )}
              </div>
            )}

            {/* Results Title/Export */}
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-border-subtle/10">
              <div className="text-[10px] uppercase tracking-widest text-text-subtle font-bold">
                Retrieved <span className="text-primary font-mono font-extrabold">{totalResults}</span> documents matching grounding criteria
              </div>
              <Button 
                variant="outline" 
                onClick={handleExportCSV}
                disabled={searchResults.length === 0}
                className="h-9"
              >
                <Download className="h-3.5 w-3.5 mr-2"/> Export CSV
              </Button>
            </div>

            {/* Results List */}
            {searchResults.length === 0 ? (
              <div className="text-center py-12 p-8 rounded-2xl bg-bg-panel/20 neu-inset-sm max-w-lg mx-auto">
                <Database className="h-8 w-8 text-primary mx-auto mb-4" />
                <h4 className="text-md font-serif italic text-text-title font-bold">No documents indexed yet</h4>
                <p className="text-xs text-text-subtle uppercase tracking-wider mt-3 max-w-md mx-auto leading-relaxed font-bold">
                  {activeGoal
                    ? "Jobs finished but returned no crawl results. Try a simpler query or check the error above."
                    : "Use AI Agent Goal Plan first to crawl and analyze the web — then standard search will query your index."}
                </p>
                {!activeGoal && mode === "search" && query && (
                  <Button 
                    type="button" 
                    onClick={() => { setMode("goal"); performSearch(query); }}
                    className="mt-5"
                  >
                    Run AI Agent Goal Plan instead
                  </Button>
                )}
              </div>
            ) : (
              searchResults.map((result) => (
                <div key={result.document_id || result.url} className="p-6 bg-bg-deep neu-outset transition-all hover:translate-y-[-2px] duration-300 cursor-pointer group rounded-2xl border-none space-y-4 mb-4 select-none">
                  <div className="flex gap-4 items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <span className="text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 bg-bg-panel/40 text-text-body border border-border-subtle/10 rounded-md">
                          {result.content_type || "web"}
                        </span>
                        <span className="text-[10px] uppercase tracking-widest text-text-subtle flex items-center gap-1 font-bold">
                          <FileText className="h-3.5 w-3.5 text-primary"/> {result.source || "searxng"}
                        </span>
                        {result.indexed_at && (
                          <span className="text-[10px] uppercase tracking-widest text-text-subtle font-bold">
                            &bull; {new Date(result.indexed_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                      <h4 className="text-lg font-serif italic text-text-title mb-2 group-hover:text-primary transition-colors">
                        {result.title}
                      </h4>
                      <p className="text-sm text-text-body line-clamp-2 leading-relaxed border-l-2 border-primary pl-4 bg-bg-panel/10 py-1 font-sans rounded-r-lg">
                        {result.main_text}
                      </p>
                      <a href={result.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center mt-3 text-[10px] font-bold text-primary hover:opacity-85 uppercase tracking-wider">
                        Source Link <ArrowRight className="h-2.5 w-2.5 ml-1" />
                      </a>
                    </div>
                    
                    <div className="shrink-0 flex flex-col items-end pl-6 border-l border-border-subtle/10 relative group/tooltip">
                      <div className="text-[9px] font-bold tracking-widest text-text-subtle uppercase mb-2 flex items-center gap-1 cursor-pointer">
                        Trust Score <span className="text-[10px]">ⓘ</span>
                      </div>
                      <div className="flex items-center gap-1.5 font-mono text-2xl font-bold">
                        {result.quality_score * 100 > 80 ? (
                          <ShieldCheck className="h-5 w-5 text-highlight-color" />
                        ) : (
                          <ShieldAlert className="h-5 w-5 text-amber-500" />
                        )}
                        <span className={result.quality_score * 100 > 80 ? "text-highlight-color" : "text-amber-500"}>
                          {Math.round(result.quality_score * 100)}
                        </span>
                      </div>
                      
                      {/* Tooltip Content */}
                      {result.ranking_details && (
                        <div className="absolute right-0 bottom-full mb-2 hidden group-hover/tooltip:block w-72 bg-bg-deep neu-outset p-4 z-50 text-xs font-sans text-left normal-case tracking-normal border-none rounded-2xl shadow-xl">
                          <h5 className="font-semibold text-text-title mb-2 uppercase tracking-wider text-[10px]">Ranking Details</h5>
                          <div className="space-y-1.5 font-mono text-[11px]">
                            <div className="flex justify-between">
                              <span className="text-text-subtle">Base Score:</span>
                              <span className="text-text-title">{result.ranking_details.base_score.toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-text-subtle">Jaccard Similarity:</span>
                              <span className="text-text-title">{result.ranking_details.jaccard_similarity.toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-text-subtle">Phrase Boost:</span>
                              <span className="text-text-title">{result.ranking_details.phrase_boost.toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between border-t border-border-subtle/10 pt-1 mt-1 font-bold">
                              <span className="text-text-subtle">Final Score:</span>
                              <span className="text-text-title">{result.ranking_details.final_score.toFixed(2)}</span>
                            </div>
                            <div className="mt-2 text-[10px] text-text-subtle font-sans leading-normal border-t border-border-subtle/10 pt-1.5">
                              <span className="font-semibold uppercase tracking-wider text-[9px] block mb-0.5">Formula</span>
                              {result.ranking_details.formula}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Analysis Sidebar Panel */}
          <div className="hidden lg:block w-80 shrink-0 bg-bg-deep neu-outset p-6 overflow-y-auto pb-8 rounded-2xl border-none">
            <h3 className="font-bold text-[10px] mb-6 border-b border-border-subtle/10 pb-3 uppercase tracking-wider text-text-subtle">Entity Extraction</h3>
            <div className="space-y-8">
              <div>
                <div className="text-[10px] uppercase tracking-widest text-text-title mb-3 font-semibold">Extracted Entities</div>
                <div className="flex flex-wrap gap-2">
                  {extractedEntities.length === 0 ? (
                    <span className="text-[9px] uppercase text-text-subtle italic">
                      {jobsStillRunning
                        ? "Extracting from research pipeline..."
                        : "No entities extracted yet"}
                    </span>
                  ) : (
                    extractedEntities.slice(0, 15).map((entity) => (
                      <span
                        key={entity.name}
                        className="text-[10px] uppercase tracking-widest font-semibold border border-border-subtle bg-bg-panel text-text-body px-2.5 py-1"
                        title={entity.type ? `${entity.type} · ${Math.round(entity.confidence * 100)}%` : undefined}
                      >
                        {entity.name}
                      </span>
                    ))
                  )}
                </div>
              </div>

              <div className="h-px bg-border-subtle"></div>

              <div>
                <div className="text-[10px] uppercase tracking-widest text-text-title mb-3 font-semibold">Active Sources</div>
                <div className="flex flex-wrap gap-2">
                  {uniqueSources.length === 0 ? (
                    <span className="text-[9px] uppercase text-text-subtle italic">
                      {jobsStillRunning ? "Collecting sources from jobs..." : "No sources tracked"}
                    </span>
                  ) : (
                    uniqueSources.map((src) => (
                      <span key={src} className="text-[10px] uppercase tracking-widest font-semibold border border-border-subtle bg-bg-panel text-text-body px-2.5 py-1">
                        {src}
                      </span>
                    ))
                  )}
                </div>
              </div>
              
              <div className="h-px bg-border-subtle"></div>

              {agentDecisions.length > 0 && (
                <>
                  <div>
                    <div className="text-[10px] uppercase tracking-widest text-text-title mb-3 font-semibold">Agent Trail</div>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {agentDecisions.map((d, i) => (
                        <div key={i} className="text-[9px] border-l-2 border-primary pl-2 py-1">
                          <span className="font-bold text-text-title uppercase">{d.agent_name}</span>
                          <p className="text-text-subtle mt-0.5 line-clamp-2">{d.reasoning}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="h-px bg-border-subtle"></div>
                </>
              )}

              <div>
                <div className="text-[10px] uppercase tracking-widest text-text-title mb-4 font-semibold">Claim Convergence</div>
                <div className="space-y-5">
                  {searchResults.length > 0 ? (
                    <>
                      <div className="text-sm">
                        <div className="text-[10px] uppercase tracking-widest font-bold text-highlight-color flex items-center mb-2">
                          <ShieldCheck className="h-3 w-3 mr-1.5"/> High Agreement
                        </div>
                        <p className="text-xs text-text-subtle leading-relaxed border-l-2 border-highlight-color pl-3 font-sans">
                          Average quality of indexed documents stands at {avgTrustScore}% reliability metrics.
                        </p>
                      </div>
                      <div className="text-sm">
                        <div className="text-[10px] uppercase tracking-widest font-bold text-amber-500 flex items-center mb-2">
                          <ShieldAlert className="h-3 w-3 mr-1.5"/> Quality State
                        </div>
                        <p className="text-xs text-text-subtle leading-relaxed border-l-2 border-amber-500 pl-3 font-sans">
                          {searchResults.length} claims registered. Check specific registries for verification mapping.
                        </p>
                      </div>
                    </>
                  ) : jobsStillRunning ? (
                    <p className="text-[9px] uppercase text-text-subtle italic">
                      Research pipeline running — convergence map after jobs complete
                    </p>
                  ) : (
                    <p className="text-[9px] uppercase text-text-subtle italic">Run search to map agreement indicators</p>
                  )}
                </div>
              </div>
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
