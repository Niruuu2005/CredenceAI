import { Link } from "react-router-dom";
import { Server, Eye, FileSpreadsheet, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Enterprise() {
  return (
    <div className="bg-bg-deep pb-32 min-h-screen text-text-body">
      <div className="pt-32 pb-24 text-center px-12 max-w-3xl mx-auto">
        <h1 className="text-5xl md:text-6xl font-serif italic mb-8 text-text-title tracking-tight">Enterprise compliance</h1>
        <p className="text-sm tracking-wide text-text-body font-sans border-l border-border-subtle pl-6 leading-relaxed text-left">
          Deploy CredenceAI in regulated financial, defense, or scientific research groups with absolute assurance, on-premise, or private VPCs.
        </p>
      </div>

      <div className="container mx-auto px-12 max-w-6xl space-y-16">
        {/* Features list */}
        <div className="grid md:grid-cols-3 gap-8">
          <div className="p-8 border border-border-subtle bg-bg-surface">
            <Server className="h-5 w-5 text-text-title mb-6" />
            <h3 className="text-lg font-serif italic text-text-title mb-3">Air-Gapped Deployment</h3>
            <p className="text-xs text-text-subtle leading-relaxed">Run the entire ingestion and model loop on private machines with complete local databases and zero egress.</p>
          </div>
          <div className="p-8 border border-border-subtle bg-bg-surface">
            <Eye className="h-5 w-5 text-text-title mb-6" />
            <h3 className="text-lg font-serif italic text-text-title mb-3">Audit Trails</h3>
            <p className="text-xs text-text-subtle leading-relaxed">Cryptographically log and track every query, analyst review, and evidence export to comply with regulatory standards.</p>
          </div>
          <div className="p-8 border border-border-subtle bg-bg-surface">
            <FileSpreadsheet className="h-5 w-5 text-text-title mb-6" />
            <h3 className="text-lg font-serif italic text-text-title mb-3">Custom Indexes</h3>
            <p className="text-xs text-text-subtle leading-relaxed">Upload internal intelligence documents, emails, and sensitive research files to integrate them into your search graphs securely.</p>
          </div>
        </div>

        {/* Contact panel */}
        <div className="border border-border-subtle bg-bg-surface">
          <div className="p-10 border-b border-border-subtle bg-bg-panel flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-serif italic text-text-title">Inquire regarding custom pilots</h3>
              <p className="text-xs text-text-subtle tracking-wider uppercase mt-1">Talk to our security representatives.</p>
            </div>
            <Mail className="h-6 w-6 text-text-subtle hidden md:block" />
          </div>
          <div className="p-10 grid md:grid-cols-2 gap-10">
            <div className="space-y-4">
              <span className="text-[10px] uppercase tracking-widest text-text-title font-bold block">Submit Inbound Request</span>
              <div className="space-y-3">
                <input placeholder="Organization Email" type="email" className="w-full bg-bg-deep border border-border-subtle px-4 py-3 text-xs text-text-body focus:outline-none focus:border-border-accent bg-bg-deep" />
                <textarea placeholder="Tell us about your technical and deployment requirements..." className="w-full bg-bg-deep border border-border-subtle px-4 py-3 text-xs text-text-body h-28 focus:outline-none focus:border-border-accent bg-bg-deep" />
                <Button className="w-full">Initialize Briefing</Button>
              </div>
            </div>
            <div className="flex flex-col justify-between border-l border-border-subtle pl-10">
              <div className="space-y-4">
                <h4 className="text-xs font-semibold text-text-title uppercase tracking-widest">Guaranteed Responses</h4>
                <p className="text-xs text-text-subtle leading-relaxed">
                  Enterprise inquiries are triaged by our systems analysts and answered within 4 business hours. We verify organization email domains before responding.
                </p>
              </div>
              <div className="text-[10px] uppercase font-mono tracking-widest text-text-subtle mt-4">
                SOC-2 TYPE II COMPLIANT • DEFENSE INDUSTRIAL BASE COMPLIANT
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
