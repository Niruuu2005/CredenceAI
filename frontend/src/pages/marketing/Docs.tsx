import { Link } from "react-router-dom";
import { Terminal, Code, ArrowUpRight } from "lucide-react";

export function Docs() {
  const sections = [
    {
      title: "Getting Started",
      items: [
        { name: "Introduction to Grounding", href: "#" },
        { name: "Executing Your First Query", href: "#" },
        { name: "Understanding Trust Scoring", href: "#" }
      ]
    },
    {
      title: "Workspace Rules",
      items: [
        { name: "Organizing Sources", href: "#" },
        { name: "Setting Up Continuous Monitors", href: "#" },
        { name: "Exporting Structured Formats", href: "#" }
      ]
    },
    {
      title: "Developer & API Reference",
      items: [
        { name: "Authentication Protocol", href: "#" },
        { name: "/v2/query Endpoint", href: "#" },
        { name: "WebSocket Alert Channels", href: "#" }
      ]
    }
  ];

  return (
    <div className="bg-bg-deep pb-32 min-h-screen text-text-body">
      <div className="pt-32 pb-24 text-center px-12 max-w-3xl mx-auto">
        <h1 className="text-5xl md:text-6xl font-serif italic mb-8 text-text-title tracking-tight">Documentation</h1>
        <p className="text-sm tracking-wide text-text-body font-sans border-l border-border-subtle pl-6 leading-relaxed text-left">
          Detailed schemas, integration guides, and syntax guides designed to help you automate deep provenance tracking at scale.
        </p>
      </div>

      <div className="container mx-auto px-12 max-w-6xl grid md:grid-cols-12 gap-12">
        {/* Sidebar */}
        <div className="md:col-span-4 space-y-8 border-r border-border-subtle pr-8">
          {sections.map((sec, i) => (
            <div key={i} className="space-y-4">
              <h4 className="text-[10px] uppercase tracking-[0.2em] font-medium text-text-title">{sec.title}</h4>
              <ul className="space-y-3 text-xs">
                {sec.items.map((item, j) => (
                  <li key={j}>
                    <a href={item.href} className="text-text-subtle hover:text-text-title transition-colors flex items-center group">
                      {item.name}
                      <ArrowUpRight className="h-3 w-3 ml-1.5 opacity-0 group-hover:opacity-100 transition-opacity text-text-title" />
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Content mock */}
        <div className="md:col-span-8 space-y-12">
          <div className="p-8 border border-border-subtle bg-bg-surface space-y-6">
            <div className="flex gap-4 items-center">
              <div className="h-10 w-10 border border-border-subtle flex items-center justify-center bg-bg-deep">
                <Terminal className="h-4 w-4 text-text-title" />
              </div>
              <div>
                <h3 className="text-lg font-serif italic text-text-title">API Example: Run Grounded Search</h3>
                <p className="text-[10px] text-text-subtle uppercase tracking-widest mt-1">Curl Request Sample</p>
              </div>
            </div>
            <pre className="p-4 bg-bg-deep border border-border-subtle text-text-body font-mono text-[11px] overflow-x-auto leading-relaxed">
{`curl -X POST "https://api.credence.ai/v2/query" \\
  -H "Authorization: Bearer $CRED_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "lithography export rules",
    "requiredProvenance": "scholarly",
    "trustThreshold": 85
  }'`}
            </pre>
          </div>

          <div className="p-8 border border-border-subtle bg-bg-surface space-y-6">
            <div className="flex gap-4 items-center">
              <div className="h-10 w-10 border border-border-subtle flex items-center justify-center bg-bg-deep">
                <Code className="h-4 w-4 text-text-title" />
              </div>
              <div>
                <h3 className="text-lg font-serif italic text-text-title font-semibold">Understanding the Response Schema</h3>
                <p className="text-[10px] text-text-subtle uppercase tracking-widest mt-1">Provenance Analysis Payload</p>
              </div>
            </div>
            <p className="text-xs text-text-body leading-relaxed">
              Every returning assertion matches an index of corroborated claims. The <code className="font-mono bg-bg-panel border border-border-subtle px-1 text-text-title">trustScore</code> represents weighted agreements across discrete publications, penalizing peer network circles and prior retractions.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
