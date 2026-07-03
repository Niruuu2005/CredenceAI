import React, { useState } from "react";
import { Server, Eye, FileSpreadsheet, Mail, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function Enterprise() {
  const [email, setEmail] = useState("");
  const [requirements, setRequirements] = useState("");
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setIsSubmitted(true);
    setEmail("");
    setRequirements("");
    setTimeout(() => {
      setIsSubmitted(false);
    }, 5000);
  };

  return (
    <div className="bg-bg-deep pb-32 min-h-screen text-text-body font-sans select-none">
      <div className="pt-32 pb-24 text-center px-12 max-w-3xl mx-auto">
        <h1 className="text-5xl md:text-6xl font-serif italic mb-8 text-text-title tracking-tight">Enterprise compliance</h1>
        <p className="text-sm tracking-wide text-text-body font-sans border-l-2 border-primary pl-6 leading-relaxed text-left">
          Deploy CredenceAI in regulated financial, defense, or scientific research groups with absolute assurance, on-premise, or private VPCs.
        </p>
      </div>

      <div className="container mx-auto px-12 max-w-6xl space-y-16">
        {/* Features list */}
        <div className="grid md:grid-cols-3 gap-8">
          <div className="p-8 rounded-2xl bg-bg-deep neu-outset border-none">
            <Server className="h-6 w-6 text-primary mb-6" />
            <h3 className="text-lg font-serif italic text-text-title mb-3">Air-Gapped Deployment</h3>
            <p className="text-xs text-text-subtle leading-relaxed">Run the entire ingestion and model loop on private machines with complete local databases and zero egress.</p>
          </div>
          <div className="p-8 rounded-2xl bg-bg-deep neu-outset border-none">
            <Eye className="h-6 w-6 text-primary mb-6" />
            <h3 className="text-lg font-serif italic text-text-title mb-3">Audit Trails</h3>
            <p className="text-xs text-text-subtle leading-relaxed">Cryptographically log and track every query, analyst review, and evidence export to comply with regulatory standards.</p>
          </div>
          <div className="p-8 rounded-2xl bg-bg-deep neu-outset border-none">
            <FileSpreadsheet className="h-6 w-6 text-primary mb-6" />
            <h3 className="text-lg font-serif italic text-text-title mb-3">Custom Indexes</h3>
            <p className="text-xs text-text-subtle leading-relaxed">Upload internal intelligence documents, emails, and sensitive research files to integrate them into your search graphs securely.</p>
          </div>
        </div>

        {/* Contact panel */}
        <div className="rounded-2xl overflow-hidden bg-bg-deep neu-outset border-none">
          <div className="p-8 md:p-10 border-b border-border-subtle/10 bg-bg-panel/40 flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-serif italic text-text-title">Inquire regarding custom pilots</h3>
              <p className="text-xs text-text-subtle tracking-wider uppercase mt-1">Talk to our security representatives.</p>
            </div>
            <Mail className="h-6 w-6 text-primary hidden md:block" />
          </div>
          <div className="p-8 md:p-10 grid md:grid-cols-2 gap-10">
            <form onSubmit={handleSubmit} className="space-y-4">
              <span className="text-[10px] uppercase tracking-widest text-text-title font-extrabold block mb-2">Submit Inbound Request</span>
              
              {isSubmitted && (
                <div className="p-3 bg-teal-500/10 border-l-4 border-teal-500 text-teal-600 dark:text-teal-400 text-xs font-semibold rounded-xl flex items-center gap-2 animate-fade-in">
                  <ShieldCheck className="h-4 w-4 shrink-0" />
                  <span>Briefing request initialized successfully. Representative will reach out shortly!</span>
                </div>
              )}

              <div className="space-y-3">
                <Input 
                  placeholder="Organization Email" 
                  type="email" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
                <textarea 
                  placeholder="Tell us about your technical and deployment requirements..." 
                  value={requirements}
                  onChange={(e) => setRequirements(e.target.value)}
                  required
                  className="w-full rounded-xl border-none bg-bg-deep neu-inset px-4 py-3 text-sm text-text-body placeholder:text-text-subtle/50 h-28 focus:outline-none focus:ring-2 focus:ring-primary/40 resize-none"
                />
                <Button type="submit" className="w-full">Initialize Briefing</Button>
              </div>
            </form>
            
            <div className="flex flex-col justify-between md:border-l border-border-subtle/10 md:pl-10">
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-text-title uppercase tracking-widest">Guaranteed Responses</h4>
                <p className="text-xs text-text-subtle leading-relaxed mt-2">
                  Enterprise inquiries are triaged by our systems analysts and answered within 4 business hours. We verify organization email domains before responding.
                </p>
              </div>
              <div className="text-[10px] uppercase font-mono tracking-widest text-text-subtle mt-8">
                SOC-2 TYPE II COMPLIANT • DEFENSE INDUSTRIAL BASE COMPLIANT
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
