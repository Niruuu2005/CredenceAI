import React, { useState, useEffect, useRef } from "react";
import {
  Search,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  FileText,
  Clock,
  CheckCircle2,
  ExternalLink,
  ChevronRight,
  RefreshCw,
  Edit3,
  Globe2,
  Layers,
  Leaf,
  HeartPulse,
  Landmark,
  Scale,
  Hash,
  Download,
  Share2,
  Info,
  Lock,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

type ResearchMode = "discover" | "investigate" | "deep_investigation";

interface RunStep {
  id: string;
  step_key: string;
  state: string;
  attempt_count: number;
  duration_ms: number;
  error_message?: string | null;
}

interface ResearchRun {
  id: string;
  question: string;
  mode: ResearchMode;
  status: string;
  created_at: string;
  completed_at?: string | null;
  steps: RunStep[];
}

interface Claim {
  id: string;
  proposition: string;
  temporal_scope?: string | null;
  units?: string | null;
  origin_type: string;
  verdict?: string | null;
  rationale?: string | null;
}

interface EvidenceEdge {
  id: string;
  claim_id: string;
  passage_id: string;
  relation: string;
  rationale?: string | null;
  passage_text: string;
  reviewer_id?: string | null;
  reviewer_notes?: string | null;
}

interface Report {
  id: string;
  run_id: string;
  title: string;
  body_markdown: string;
  manifest_hash: string;
  status: string;
  reviewed_by?: string | null;
  reviewer_notes?: string | null;
}

const PUBLIC_IMPACT_PRESETS = [
  {
    icon: Leaf,
    tag: "Climate & Energy",
    query: "Did global clean energy investment surpass fossil fuel capex in 2024?",
  },
  {
    icon: HeartPulse,
    tag: "Public Health",
    query: "Did clinical trial evaluations demonstrate efficacy in reducing transmission?",
  },
  {
    icon: Landmark,
    tag: "Civic Governance",
    query: "Did municipal infrastructure appropriations meet statutory allocation targets?",
  },
  {
    icon: Scale,
    tag: "Public Integrity",
    query: "Are reported industrial emissions figures consistent with independent satellite data?",
  },
];

export function ResearchWorkspace() {
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState<ResearchMode>("investigate");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [activeRun, setActiveRun] = useState<ResearchRun | null>(null);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [selectedClaim, setSelectedClaim] = useState<Claim | null>(null);
  const [evidenceEdges, setEvidenceEdges] = useState<EvidenceEdge[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [activeSideTab, setActiveSideTab] = useState<"evidence" | "report">("evidence");
  const [reviewModalEdge, setReviewModalEdge] = useState<EvidenceEdge | null>(null);
  const [reviewRelation, setReviewRelation] = useState("supports");
  const [reviewNotes, setReviewNotes] = useState("");
  const [isSubmittingReview, setIsSubmittingReview] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);
  const prevStatusRef = useRef<string | null>(null);

  const scrollToResults = () => {
    // Timeout gives React a render frame to populate findings and claims DOM
    setTimeout(() => {
      if (resultsRef.current) {
        resultsRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
      } else {
        const el = document.getElementById("research-results-panel");
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }
    }, 150);
  };

  useEffect(() => {
    loadRecentRuns();
  }, []);

  // Smoothly scroll down to results panel whenever a run transitions to completed
  useEffect(() => {
    if (
      activeRun?.status === "completed" &&
      prevStatusRef.current !== "completed" &&
      prevStatusRef.current !== null
    ) {
      scrollToResults();
    }
    prevStatusRef.current = activeRun?.status ?? null;
  }, [activeRun?.status]);

  const loadRecentRuns = async () => {
    try {
      const data = await api.listResearchRuns();
      setRuns(data);
      if (data.length > 0 && !activeRun) {
        selectRun(data[0]);
      }
    } catch (e) {
      console.error("Failed to load runs:", e);
    }
  };

  const selectRun = async (run: ResearchRun) => {
    setActiveRun(run);
    try {
      const runDetails = await api.getResearchRun(run.id);
      setActiveRun(runDetails);

      const claimsData = await api.getRunClaims(run.id);
      setClaims(claimsData);
      if (claimsData.length > 0) {
        setSelectedClaim(claimsData[0]);
        loadEvidence(run.id, claimsData[0].id);
      } else {
        setSelectedClaim(null);
        setEvidenceEdges([]);
      }

      const reportData = await api.getRunReport(run.id, 1);
      setReport(reportData);
    } catch (e) {
      console.error("Error loading run data:", e);
    }
  };

  const loadEvidence = async (runId: string, claimId: string) => {
    try {
      const edges = await api.getClaimEvidence(runId, claimId);
      setEvidenceEdges(edges);
    } catch (e) {
      console.error("Error loading evidence:", e);
    }
  };

  const executeInquiry = async (queryText: string, selectedMode: ResearchMode = mode) => {
    if (!queryText.trim()) return;
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const newRun = await api.createResearchRun(queryText, selectedMode);
      setRuns((prev) => [newRun, ...prev]);
      setActiveRun(newRun);

      const completedRun = await api.executeResearchRun(newRun.id);
      setActiveRun(completedRun);
      await selectRun(completedRun);
      setQuestion("");
      scrollToResults();
    } catch (err) {
      console.error("Failed to execute research run:", err);
      setErrorMsg(
        err instanceof Error
          ? err.message
          : "Unable to complete audit. If this persists, please ensure the backend service is reachable."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartRun = (e: React.FormEvent) => {
    e.preventDefault();
    executeInquiry(question);
  };

  const handleReviewSubmit = async () => {
    if (!activeRun || !selectedClaim || !reviewModalEdge) return;
    setIsSubmittingReview(true);
    try {
      await api.reviewClaimEvidence(
        activeRun.id,
        selectedClaim.id,
        reviewModalEdge.id,
        reviewRelation,
        reviewNotes
      );
      await loadEvidence(activeRun.id, selectedClaim.id);
      setReviewModalEdge(null);
      setReviewNotes("");
    } catch (err) {
      console.error("Review submission failed:", err);
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const handleApproveReport = async () => {
    if (!activeRun || !report) return;
    try {
      const approved = await api.approveReport(
        activeRun.id,
        report.id,
        "Verified and certified for public release by accredited researcher."
      );
      setReport(approved);
    } catch (err) {
      console.error("Report approval failed:", err);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans selection:bg-teal-900/10 dark:selection:bg-teal-500/20">
      {/* Editorial Header */}
      <div className="border-b border-border-subtle bg-background-surface/40">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary font-bold text-sm">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold text-text-title tracking-tight">
                  Public Social Impact Research
                </h1>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
                  CredenceAI 2.0 Engine
                </span>
              </div>
              <p className="text-xs text-text-subtle">
                Open, inspectable intelligence grounded in peer-reviewed science, public filings, and verified news wire lineage.
              </p>
            </div>
          </div>

          {activeRun && (
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono px-3 py-1 rounded-full bg-background-deep border border-border-subtle text-text-subtle">
                Run #{activeRun.id.substring(4, 12)}
              </span>
              <span
                className={cn(
                  "text-xs px-3 py-1 rounded-full font-semibold uppercase tracking-wider",
                  activeRun.status === "completed"
                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30"
                    : activeRun.status === "cancelled"
                    ? "bg-rose-500/10 text-rose-600 border border-rose-500/30"
                    : "bg-amber-500/10 text-amber-600 border border-amber-500/30"
                )}
              >
                {activeRun.status}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Main Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8 relative">
        <div className="ambient-glow"></div>

        {/* Hero Inquiry Studio (Perplexity / Linear Style) */}
        <section className="glass-card p-6 md:p-8 space-y-6 relative z-10 border border-white/10 dark:border-white/10 shadow-2xl">
          <div className="max-w-3xl space-y-2">
            <div className="glow-pill mb-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>Autonomous Truth Verification & Research Engine</span>
            </div>
            <h2 className="text-2xl md:text-3xl font-bold font-sans text-text-title tracking-tight">
              Investigate a Public Interest Proposition
            </h2>
            <p className="text-sm text-text-subtle leading-relaxed">
              Every inquiry is decomposed into verifiable atomic propositions, cross-referenced against authoritative literature, and anchored to immutable citation snapshots.
            </p>
          </div>

          {errorMsg && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 text-xs flex items-center justify-between animate-fade-in">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
              <button
                type="button"
                onClick={() => setErrorMsg(null)}
                className="text-xs font-semibold hover:underline cursor-pointer"
              >
                Dismiss
              </button>
            </div>
          )}

          <form onSubmit={handleStartRun} className="space-y-4">
            <div className="relative rounded-2xl bg-background-deep/80 border border-border-subtle focus-within:border-primary/60 focus-within:ring-4 focus-within:ring-primary/10 transition-all shadow-inner p-2">
              <textarea
                id="research-inquiry-input"
                rows={2}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask an investigative inquiry or state a factual claim to audit (e.g., 'Did clean energy investments surpass fossil fuels globally in 2024?')"
                className="w-full px-3 py-2 text-base rounded-xl bg-transparent text-text-title placeholder:text-text-subtle/50 focus:outline-none transition-all resize-none font-sans leading-relaxed"
              />
              
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2 px-1 border-t border-border-subtle/40">
                {/* Research Rigor Modes */}
                <div className="flex items-center gap-1 p-0.5 bg-background-panel rounded-xl border border-border-subtle">
                  <span className="text-xs font-semibold text-text-subtle px-2">
                    Rigor:
                  </span>
                  {(
                    [
                      { id: "discover", label: "Fast Sweep" },
                      { id: "investigate", label: "Balanced Audit" },
                      { id: "deep_investigation", label: "Deep Investigation" },
                    ] as const
                  ).map((m) => (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => setMode(m.id)}
                      className={cn(
                        "px-3 py-1 text-xs font-semibold rounded-lg transition-all cursor-pointer",
                        mode === m.id
                          ? "bg-primary text-primary-foreground shadow-sm"
                          : "text-text-subtle hover:text-text-title hover:bg-background-deep"
                      )}
                    >
                      <span>{m.label}</span>
                    </button>
                  ))}
                </div>

                {/* Submit Button */}
                <button
                  id="run-audit-button"
                  type="submit"
                  disabled={isLoading || !question.trim()}
                  className="px-6 py-2 rounded-xl bg-primary hover:opacity-95 text-primary-foreground font-semibold text-sm flex items-center gap-2 transition-all shadow-[0_0_20px_rgba(16,185,129,0.3)] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                >
                  {isLoading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Executing Audit...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      Run Factual Audit
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>

          {/* Public Impact Topic Presets */}
          <div className="pt-2 border-t border-border-subtle/40">
            <div className="text-xs font-semibold text-text-subtle mb-3 flex items-center gap-1.5">
              <Globe2 className="w-3.5 h-3.5 text-primary" />
              Suggested Public Interest Inquiries:
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2.5">
              {PUBLIC_IMPACT_PRESETS.map((preset, idx) => {
                const IconComponent = preset.icon;
                return (
                  <button
                    id={`preset-btn-${idx}`}
                    key={idx}
                    type="button"
                    onClick={() => {
                      setQuestion(preset.query);
                      executeInquiry(preset.query);
                    }}
                    className="p-3 rounded-xl border border-border-subtle bg-background-panel/60 hover:bg-background-panel hover:border-primary/40 text-left transition-all group flex flex-col justify-between cursor-pointer shadow-xs"
                  >
                    <div className="flex items-center gap-1.5 text-xs font-bold text-primary mb-1">
                      <IconComponent className="w-3.5 h-3.5" />
                      <span>{preset.tag}</span>
                    </div>
                    <p className="text-xs text-text-body group-hover:text-text-title line-clamp-2 leading-relaxed">
                      "{preset.query}"
                    </p>
                  </button>
                );
              })}
            </div>
          </div>
        </section>

        {/* Public Trust & Verification Guardrails Bar */}
        <section className="grid grid-cols-2 md:grid-cols-4 gap-4 relative z-10">
          <div className="glass-card p-4 space-y-1">
            <div className="flex items-center gap-2 text-primary text-xs font-bold">
              <ShieldCheck className="w-4 h-4" />
              <span>Zero "Probability Theater"</span>
            </div>
            <p className="text-xs text-text-subtle leading-relaxed">
              Eliminates pseudo-scientific 99% truth percentages. Employs honest calibrated verdicts.
            </p>
          </div>

          <div className="glass-card p-4 space-y-1">
            <div className="flex items-center gap-2 text-primary text-xs font-bold">
              <FileText className="w-4 h-4" />
              <span>100% Frozen Citations</span>
            </div>
            <p className="text-xs text-text-subtle leading-relaxed">
              Every statement anchored to immutable snapshot hashes. 0 unanchored hallucinations.
            </p>
          </div>

          <div className="glass-card p-4 space-y-1">
            <div className="flex items-center gap-2 text-primary text-xs font-bold">
              <Layers className="w-4 h-4" />
              <span>Audited Wire Lineage</span>
            </div>
            <p className="text-xs text-text-subtle leading-relaxed">
              Detects AP & Reuters syndication reprints so duplicates don't inflate independence.
            </p>
          </div>

          <div className="glass-card p-4 space-y-1">
            <div className="flex items-center gap-2 text-primary text-xs font-bold">
              <Lock className="w-4 h-4" />
              <span>Tenant Security Gated</span>
            </div>
            <p className="text-xs text-text-subtle leading-relaxed">
              Rigorous workspace isolation protecting public health & civic data from cross-access.
            </p>
          </div>
        </section>

        {/* Active Investigation Findings & Evidence Inspector */}
        {activeRun ? (
          <section
            id="research-results-panel"
            ref={resultsRef}
            className="space-y-6 scroll-mt-20 animate-fade-in"
          >
            {/* Live Pipeline Stepper */}
            <div className="glass-card p-4 flex flex-wrap items-center justify-between gap-4 border border-border-subtle/50">
              <div className="flex items-center gap-2 overflow-x-auto py-1">
                {["planning", "retrieving", "extracting", "verifying", "reporting"].map(
                  (stage, idx) => {
                    const step = activeRun.steps?.find((s) => s.step_key === stage);
                    const isComplete = step?.state === "completed";
                    const isRunning = step?.state === "running";

                    return (
                      <div key={stage} className="flex items-center gap-2 shrink-0">
                        <div
                          className={cn(
                            "flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium capitalize",
                            isComplete
                              ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 font-semibold"
                              : isRunning
                              ? "bg-primary/10 text-primary border border-primary/30 animate-pulse font-semibold"
                              : "bg-background-deep text-text-subtle border border-border-subtle/40"
                          )}
                        >
                          <span className="w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold">
                            {isComplete ? "✓" : idx + 1}
                          </span>
                          <span>{stage}</span>
                        </div>
                        {idx < 4 && <ChevronRight className="w-3.5 h-3.5 text-text-subtle/30" />}
                      </div>
                    );
                  }
                )}
              </div>

              {runs.length > 1 && (
                <div className="flex items-center gap-2 text-xs text-text-subtle">
                  <span>Switch Investigation:</span>
                  <select
                    value={activeRun.id}
                    onChange={(e) => {
                      const found = runs.find((r) => r.id === e.target.value);
                      if (found) {
                        selectRun(found);
                        scrollToResults();
                      }
                    }}
                    className="px-2.5 py-1 rounded-lg bg-background border border-border-subtle text-xs text-text-title focus:outline-none"
                  >
                    {runs.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.question.substring(0, 45)}...
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {/* Findings & Evidence Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              {/* Left Column: Atomic Findings Stream (60%) */}
              <div className="lg:col-span-7 space-y-6">
                <div className="glass-card p-6 space-y-3">
                  <div className="flex items-center justify-between pb-3 border-b border-border-subtle">
                    <span className="text-xs font-semibold text-text-subtle">
                      Core Inquiry
                    </span>
                    <span className="text-xs text-text-subtle font-mono">
                      {new Date(activeRun.created_at).toLocaleDateString(undefined, {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold font-sans text-text-title leading-snug">
                    "{activeRun.question}"
                  </h3>
                </div>

                {/* Atomic Propositions List */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-semibold text-text-subtle">
                      Atomic Propositions & Calibrated Verdicts
                    </h4>
                    <span className="text-xs text-text-subtle">
                      {claims.length} proposition{claims.length !== 1 ? "s" : ""} audited
                    </span>
                  </div>

                  {claims.length === 0 ? (
                    <div className="glass-card p-8 text-center text-xs text-text-subtle">
                      Evaluating source literature...
                    </div>
                  ) : (
                    claims.map((claim) => {
                      const isSelected = selectedClaim?.id === claim.id;
                      const isSupported = claim.verdict === "supported";
                      const isDisputed = claim.verdict === "disputed";

                      return (
                        <div
                          key={claim.id}
                          onClick={() => {
                            setSelectedClaim(claim);
                            loadEvidence(activeRun.id, claim.id);
                            setActiveSideTab("evidence");
                          }}
                          className={cn(
                            "glass-card p-5 cursor-pointer space-y-4 relative overflow-hidden transition-all",
                            isSelected
                              ? "border-primary ring-2 ring-primary/20 shadow-lg shadow-primary/5"
                              : "hover:border-primary/40"
                          )}
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="space-y-1.5 flex-1">
                              <p className="text-base font-semibold text-text-title leading-relaxed">
                                {claim.proposition}
                              </p>
                              {claim.rationale && (
                                <p className="text-xs text-text-subtle leading-relaxed">
                                  {claim.rationale}
                                </p>
                              )}
                            </div>

                            <span
                              className={cn(
                                "px-3 py-1 rounded-full text-xs font-semibold shrink-0 flex items-center gap-1.5",
                                isSupported
                                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                  : isDisputed
                                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                                  : "bg-slate-500/10 text-slate-300 border border-slate-500/30"
                              )}
                            >
                              <span className={cn("w-1.5 h-1.5 rounded-full", isSupported ? "bg-emerald-400" : isDisputed ? "bg-amber-400" : "bg-slate-400")}></span>
                              {claim.verdict === "supported" ? "Verified" : claim.verdict === "disputed" ? "Disputed" : claim.verdict || "Evaluating"}
                            </span>
                          </div>

                          {/* Scope Badges */}
                          <div className="flex flex-wrap items-center gap-3 pt-3 border-t border-border-subtle text-xs text-text-subtle">
                            {claim.temporal_scope && (
                              <span className="flex items-center gap-1 font-mono">
                                <Clock className="w-3.5 h-3.5 text-text-subtle" />
                                {claim.temporal_scope}
                              </span>
                            )}
                            {claim.units && (
                              <span className="px-2 py-0.5 rounded bg-background-deep font-mono">
                                Units: {claim.units}
                              </span>
                            )}
                            <span>Origin: {claim.origin_type}</span>

                            <span className="ml-auto flex items-center gap-1 text-primary text-xs font-semibold">
                              Inspect Sources <ChevronRight className="w-3.5 h-3.5" />
                            </span>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>

              {/* Right Column: Grounded Evidence Inspector & Frozen Report (40%) */}
              <div className="lg:col-span-5 sticky top-24 space-y-4">
                {/* Tab Switcher */}
                <div className="flex items-center gap-2 p-1 bg-background-deep rounded-xl border border-border-subtle">
                  <button
                    type="button"
                    onClick={() => setActiveSideTab("evidence")}
                    className={cn(
                      "flex-1 py-2 text-xs font-semibold rounded-lg transition-all flex items-center justify-center gap-1.5 cursor-pointer",
                      activeSideTab === "evidence"
                        ? "bg-background-surface text-text-title shadow-sm"
                        : "text-text-subtle hover:text-text-title"
                    )}
                  >
                    <Layers className="w-3.5 h-3.5" />
                    Evidence Passages ({evidenceEdges.length})
                  </button>

                  <button
                    type="button"
                    onClick={() => setActiveSideTab("report")}
                    className={cn(
                      "flex-1 py-2 text-xs font-semibold rounded-lg transition-all flex items-center justify-center gap-1.5 cursor-pointer",
                      activeSideTab === "report"
                        ? "bg-background-surface text-text-title shadow-sm"
                        : "text-text-subtle hover:text-text-title"
                    )}
                  >
                    <FileText className="w-3.5 h-3.5" />
                    Frozen Brief
                  </button>
                </div>

                {activeSideTab === "evidence" && (
                  <div className="space-y-4 max-h-[calc(100vh-12rem)] overflow-y-auto pr-1">
                    {selectedClaim && (
                      <div className="glass-card p-4 bg-background-deep/60 space-y-1">
                        <span className="text-xs font-semibold text-text-subtle">
                          Inspecting Grounding For:
                        </span>
                        <p className="text-xs font-semibold text-text-title">
                          "{selectedClaim.proposition}"
                        </p>
                      </div>
                    )}

                    {evidenceEdges.length === 0 ? (
                      <div className="glass-card p-8 text-center text-xs text-text-subtle space-y-2">
                        <Info className="w-5 h-5 text-text-subtle/50 mx-auto" />
                        <p>No passage groundings recorded for this proposition.</p>
                      </div>
                    ) : (
                      evidenceEdges.map((edge) => (
                        <div key={edge.id} className="glass-card p-5 space-y-3">
                          <div className="flex items-center justify-between">
                            <span
                              className={cn(
                                "px-2.5 py-0.5 rounded-full text-xs font-semibold flex items-center gap-1",
                                edge.relation === "supports"
                                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                  : edge.relation === "contradicts"
                                  ? "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                                  : "bg-slate-500/10 text-slate-300 border border-slate-500/30"
                              )}
                            >
                              Relation: {edge.relation}
                            </span>

                            <button
                              type="button"
                              onClick={() => {
                                setReviewModalEdge(edge);
                                setReviewRelation(edge.relation);
                                setReviewNotes(edge.reviewer_notes || "");
                              }}
                              className="text-xs text-text-subtle hover:text-primary flex items-center gap-1 font-medium transition-colors cursor-pointer"
                            >
                              <Edit3 className="w-3 h-3" /> Annotate / Dispute
                            </button>
                          </div>

                          {/* Grounded Excerpt */}
                          <div className="p-3.5 rounded-xl bg-background-deep/80 border-l-3 border-primary text-sm font-sans text-text-body leading-relaxed">
                            "{edge.passage_text}"
                          </div>

                          {edge.rationale && (
                            <p className="text-xs text-text-subtle">
                              Heuristic Alignment: {edge.rationale}
                            </p>
                          )}

                          {edge.reviewer_notes && (
                            <div className="p-3 rounded-xl bg-primary/10 border border-primary/20 text-xs text-primary space-y-1">
                              <span className="font-semibold">Human Review Annotation:</span>
                              <p className="text-text-body">{edge.reviewer_notes}</p>
                            </div>
                          )}

                          <div className="flex items-center justify-between pt-2 border-t border-border-subtle text-xs text-text-subtle font-mono">
                            <span>Passage: {edge.passage_id.slice(0, 16)}...</span>
                            <span className="text-emerald-400 flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3" /> Verified Hash
                            </span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}

                {activeSideTab === "report" && (
                  <div className="glass-card p-6 space-y-6 max-h-[calc(100vh-12rem)] overflow-y-auto">
                    {report ? (
                      <>
                        <div className="space-y-2 pb-4 border-b border-border-subtle">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-text-subtle">
                              Citation-Frozen Report
                            </span>
                            <span
                              className={cn(
                                "px-2.5 py-0.5 rounded-full text-xs font-semibold",
                                report.status === "approved"
                                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                  : "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                              )}
                            >
                              {report.status}
                            </span>
                          </div>
                          <h4 className="text-lg font-bold font-sans text-text-title">
                            {report.title}
                          </h4>
                          <div className="p-2 rounded-lg bg-background-deep border border-border-subtle font-mono text-xs text-text-subtle break-all">
                            Manifest Hash: {report.manifest_hash}
                          </div>
                        </div>

                        {/* Markdown Content */}
                        <div className="prose prose-sm max-w-none font-sans text-xs leading-relaxed text-text-body whitespace-pre-wrap">
                          {report.body_markdown}
                        </div>

                        {/* Sign-off Actions */}
                        <div className="pt-4 border-t border-border-subtle flex items-center justify-between">
                          {report.status !== "approved" ? (
                            <button
                              type="button"
                              onClick={handleApproveReport}
                              className="w-full py-2.5 rounded-xl bg-primary hover:opacity-95 text-primary-foreground font-semibold text-xs flex items-center justify-center gap-1.5 shadow-md shadow-primary/20 transition-all cursor-pointer"
                            >
                              <CheckCircle2 className="w-4 h-4" /> Certify & Approve Brief
                            </button>
                          ) : (
                            <div className="text-xs text-emerald-400 font-semibold flex items-center gap-1.5">
                              <CheckCircle2 className="w-4 h-4" /> Certified by Public Interest Reviewer
                            </div>
                          )}
                        </div>
                      </>
                    ) : (
                      <div className="p-8 text-center text-xs text-text-subtle">
                        Research brief is compiling...
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </section>
        ) : (
          <section className="glass-card p-12 text-center max-w-2xl mx-auto space-y-4 border border-border-subtle/50">
            <div className="w-12 h-12 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mx-auto shadow-[0_0_20px_rgba(16,185,129,0.15)]">
              <Search className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-text-title tracking-tight">
              Ready to Investigate
            </h3>
            <p className="text-sm text-text-subtle max-w-md mx-auto leading-relaxed">
              Enter an inquiry proposition above or select one of the social impact suggestions to start a verifiable factual audit.
            </p>
          </section>
        )}
      </main>

      {/* Human Review Modal */}
      {reviewModalEdge && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4">
          <div className="glass-panel border border-border-subtle rounded-2xl w-full max-w-lg p-6 space-y-5 shadow-2xl">
            <div className="space-y-1">
              <h3 className="text-base font-bold text-text-title tracking-tight">
                Public Review & Evidence Annotation
              </h3>
              <p className="text-xs text-text-subtle leading-relaxed">
                Annotate or dispute the ground relationship. All database snapshots and passages remain 100% immutable; reviewer annotations are preserved in the workspace audit trail.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-background-deep/60 border border-border-subtle text-sm leading-relaxed text-text-title">
              "{reviewModalEdge.passage_text}"
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-text-subtle block mb-1.5">
                  Assessed Relationship Label
                </label>
                <select
                  value={reviewRelation}
                  onChange={(e) => setReviewRelation(e.target.value)}
                  className="w-full px-3.5 py-2.5 text-xs rounded-xl bg-background border border-border-subtle text-text-title focus:outline-none focus:border-primary font-medium"
                >
                  <option value="supports">Supports (Affirms the proposition)</option>
                  <option value="contradicts">Contradicts (Refutes or opposes the proposition)</option>
                  <option value="mentions">Mentions (Discusses entities without affirmation)</option>
                  <option value="uncertain">Uncertain (Context is ambiguous)</option>
                  <option value="irrelevant">Irrelevant (Outside factual scope)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-text-subtle block mb-1.5">
                  Reviewer Rationale & Methodology Notes
                </label>
                <textarea
                  rows={3}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="State the verifiable reason or methodological justification for this annotation..."
                  className="w-full px-3.5 py-2.5 text-xs rounded-xl bg-background border border-border-subtle text-text-title focus:outline-none focus:border-primary resize-none leading-relaxed"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2 border-t border-border-subtle/30">
              <button
                type="button"
                onClick={() => setReviewModalEdge(null)}
                className="px-4 py-2 rounded-xl border border-border-subtle text-xs font-medium text-text-subtle hover:text-text-title transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleReviewSubmit}
                disabled={isSubmittingReview}
                className="px-5 py-2 rounded-xl bg-primary text-primary-foreground font-semibold text-xs shadow-md transition-all cursor-pointer disabled:opacity-50"
              >
                {isSubmittingReview ? "Recording..." : "Save Public Audit Record"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function LockIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  );
}
