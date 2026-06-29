import React, { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ShieldCheck, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Legal() {
  const [searchParams, setSearchParams] = useSearchParams();
  const currentTab = searchParams.get("tab") || "terms";

  const handleTabChange = (tab: string) => {
    setSearchParams({ tab });
  };

  return (
    <div className="bg-bg-deep pb-32 min-h-screen text-text-body">
      <div className="pt-32 pb-16 text-center px-12 max-w-3xl mx-auto">
        <h1 className="text-5xl md:text-6xl font-serif italic mb-6 text-text-title tracking-tight">Legal & Trust</h1>
        <p className="text-xs uppercase tracking-[0.2em] text-text-subtle font-bold mb-8">Credence Security and Compliance Core</p>
      </div>

      <div className="container mx-auto px-12 max-w-5xl">
        {/* Tab buttons */}
        <div className="flex border-b border-border-subtle mb-12">
          <button 
            onClick={() => handleTabChange("terms")}
            className={`px-6 py-3 text-xs uppercase tracking-widest font-bold border-b-2 transition-all cursor-pointer ${currentTab === "terms" ? "border-text-title text-text-title font-semibold" : "border-transparent text-text-subtle hover:text-text-title"}`}
          >
            Terms of Service
          </button>
          <button 
            onClick={() => handleTabChange("privacy")}
            className={`px-6 py-3 text-xs uppercase tracking-widest font-bold border-b-2 transition-all cursor-pointer ${currentTab === "privacy" ? "border-text-title text-text-title font-semibold" : "border-transparent text-text-subtle hover:text-text-title"}`}
          >
            Privacy Policy
          </button>
          <button 
            onClick={() => handleTabChange("security")}
            className={`px-6 py-3 text-xs uppercase tracking-widest font-bold border-b-2 transition-all cursor-pointer ${currentTab === "security" ? "border-text-title text-text-title font-semibold" : "border-transparent text-text-subtle hover:text-text-title"}`}
          >
            Security Controls
          </button>
        </div>

        <div className="grid md:grid-cols-12 gap-12">
          {/* Main Content */}
          <div className="md:col-span-8 text-text-body text-xs leading-relaxed space-y-6">
            {currentTab === "terms" && (
              <div className="space-y-6">
                <h3 className="text-2xl font-serif italic text-text-title mb-4">Terms of Service</h3>
                <p className="font-semibold text-text-title">Last updated: June 18, 2026</p>
                <p>
                  Welcome to CredenceAI. These Terms of Service ("Terms") govern your access to and use of our research intelligence platform, including any website content, API integrations, and applications.
                </p>
                <h4 className="text-sm font-semibold text-text-title uppercase tracking-wider mt-6">1. Access and License Clauses</h4>
                <p>
                  We grant you a non-transferable, non-exclusive, revocable license to access our platform solely for professional research and intelligence-gathering purposes.
                </p>
                <h4 className="text-sm font-semibold text-text-title uppercase tracking-wider mt-6">2. Permitted Use Only</h4>
                <p>
                  You agree to use our platform only in accordance with all applicable international, local laws and regulatory export frameworks. Reverse engineering our claim scoring models or using web-scraping to replicate our indexes is strictly prohibited.
                </p>
              </div>
            )}

            {currentTab === "privacy" && (
              <div className="space-y-6">
                <h3 className="text-2xl font-serif italic text-text-title mb-4">Privacy Policy</h3>
                <p className="font-semibold text-text-title">Last updated: June 18, 2026</p>
                <p>
                  At Credence, trust-first research implies that your intelligence queries are entirely secure. This Privacy Policy details our isolation standards of analytical tasks.
                </p>
                <h4 className="text-sm font-semibold text-text-title uppercase tracking-wider mt-6">1. Zero Query Retention Options</h4>
                <p>
                  For qualifying tiers, we operate on a strict zero-retention foundation. Search queries represent trade secrets or classified research pipelines; therefore, we neither train downstream models on your queries nor write raw string text into persistent logs.
                </p>
                <h4 className="text-sm font-semibold text-text-title uppercase tracking-wider mt-6">2. Third-Party Interfaces</h4>
                <p>
                  When fetching real-time search data or scientific publications, all queries are routed through corporate proxies scrubbing any metadata identifying your account.
                </p>
              </div>
            )}

            {currentTab === "security" && (
              <div className="space-y-6">
                <h3 className="text-2xl font-serif italic text-text-title mb-4">Security Controls</h3>
                <p className="font-semibold text-text-title">Last updated: June 18, 2026</p>
                <p>
                  Every request, document upload, and dynamic monitor matches maximum security paradigms. Learn about the physical, network, and application defenses safeguarding your research.
                </p>
                <h4 className="text-sm font-semibold text-text-title uppercase tracking-wider mt-6">1. Encryption Protocols</h4>
                <p>
                  All data in transit is encrypted using TLS 1.3 with Perfect Forward Secrecy, while static databases use AES-256 with isolated key rotations in Hardware Security Modules (HSMs).
                </p>
                <h4 className="text-sm font-semibold text-text-title uppercase tracking-wider mt-6">2. Isolated Sandbox Containers</h4>
                <p>
                  Any execution for private file summaries or document uploads is isolated inside a sandboxed micro-container with automated self-termination on session close.
                </p>
              </div>
            )}
          </div>

          {/* Right sidebar info */}
          <div className="md:col-span-4 p-6 border border-border-subtle bg-bg-surface space-y-6 h-fit bg-bg-surface">
            <h4 className="text-[10px] uppercase tracking-[0.2em] font-medium text-text-title">Trust Compliance</h4>
            <div className="space-y-4 text-xs font-sans">
              <div className="flex items-start gap-3">
                <ShieldCheck className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                <div>
                  <span className="font-medium text-text-title block">SOC-2 Type II Certified</span>
                  <p className="text-[10px] text-text-subtle mt-1">Sustaining continuous operational excellence audits.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Lock className="h-4 w-4 text-text-subtle shrink-0 mt-0.5" />
                <div>
                  <span className="font-medium text-text-title block">ISO 27001 Foundation</span>
                  <p className="text-[10px] text-text-subtle mt-1">Aligned with international standards for security systems.</p>
                </div>
              </div>
            </div>
            
            <div className="pt-6 border-t border-border-subtle text-center">
              <Button asChild size="sm" variant="outline" className="w-full border-border-subtle bg-bg-deep hover:bg-bg-panel hover:text-text-title">
                <Link to="/auth/sign-up">Create Secure Account</Link>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
