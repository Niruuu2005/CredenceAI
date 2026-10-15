import { Link } from "react-router-dom";
import { Terminal, Code, ArrowUpRight } from "lucide-react";

const DOC_BASE = "https://github.com/Niruuu2005/CredenceAI/blob/main/docs";

export function Docs() {
  const sections = [
    {
      title: "Getting Started",
      items: [
        { name: "Introduction", href: `${DOC_BASE}/simple_explanation.md` },
        { name: "Backend Setup", href: `${DOC_BASE}/backend.md` },
        { name: "Frontend Setup", href: `${DOC_BASE}/frontend.md` },
      ]
    },
    {
      title: "Workspace",
      items: [
        { name: "Collections & Monitors", href: `${DOC_BASE}/api.md` },
        { name: "Environment Variables", href: `${DOC_BASE}/environment.md` },
        { name: "Deployment Guide", href: `${DOC_BASE}/deployment.md` },
      ]
    },
    {
      title: "Developer & API",
      items: [
        { name: "API Reference", href: `${DOC_BASE}/api.md` },
        { name: "SDK Guide", href: `${DOC_BASE}/sdk.md` },
        { name: "Architecture", href: `${DOC_BASE}/architecture.md` },
      ]
    }
  ];

  return (
    <div className="bg-bg-deep pb-32 min-h-screen text-text-body">
      <div className="pt-32 pb-24 text-center px-12 max-w-3xl mx-auto">
        <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6 text-text-title">Documentation</h1>
        <p className="text-sm tracking-wide text-text-body font-sans border-l-2 border-primary/40 pl-6 leading-relaxed text-left">
          Integration guides, API reference, and deployment docs for CredenceAI search intelligence.
        </p>
      </div>

      <div className="container mx-auto px-12 max-w-6xl grid md:grid-cols-12 gap-12">
        <div className="md:col-span-4 space-y-8 border-r border-border-subtle pr-8">
          {sections.map((sec, i) => (
            <div key={i} className="space-y-4">
              <h4 className="text-xs uppercase tracking-wider font-semibold text-text-title">{sec.title}</h4>
              <ul className="space-y-3 text-xs">
                {sec.items.map((item, j) => (
                  <li key={j}>
                    <a href={item.href} target="_blank" rel="noopener noreferrer" className="text-text-subtle hover:text-text-title transition-colors flex items-center group font-medium">
                      {item.name}
                      <ArrowUpRight className="h-3 w-3 ml-1.5 opacity-0 group-hover:opacity-100 transition-opacity text-primary" />
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="md:col-span-8 space-y-8">
          <div className="p-8 border border-border-subtle bg-background-surface rounded-2xl shadow-card space-y-6">
            <div className="flex gap-4 items-center">
              <div className="h-10 w-10 border border-border-subtle rounded-xl flex items-center justify-center bg-background-deep text-primary">
                <Terminal className="h-4 w-4" />
              </div>
              <div>
                <h3 className="text-lg font-bold tracking-tight text-text-title">API Example: Submit Search Job</h3>
                <p className="text-xs text-text-subtle font-medium mt-0.5">Curl Request Sample</p>
              </div>
            </div>
            <pre className="p-4 bg-background-deep rounded-xl border border-border-subtle text-text-body font-mono text-xs overflow-x-auto leading-relaxed">
{`curl -X POST "https://credenceai-api.onrender.com/api/jobs" \\
  -H "Authorization: Bearer $CRED_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "job_type": "search_query",
    "input": "lithography export rules",
    "execution_mode": "standard"
  }'`}
            </pre>
          </div>

          <div className="p-8 border border-border-subtle bg-background-surface rounded-2xl shadow-card space-y-6">
            <div className="flex gap-4 items-center">
              <div className="h-10 w-10 border border-border-subtle rounded-xl flex items-center justify-center bg-background-deep text-primary">
                <Code className="h-4 w-4" />
              </div>
              <div>
                <h3 className="text-lg font-bold tracking-tight text-text-title font-semibold">AI Goal Research</h3>
                <p className="text-xs text-text-subtle font-medium mt-0.5">Multi-agent decomposition</p>
              </div>
            </div>
            <p className="text-xs text-text-body leading-relaxed font-medium">
              Use <code className="font-mono bg-background-deep border border-border-subtle px-1.5 py-0.5 rounded text-primary">POST /api/goals</code> to
              decompose complex research questions into parallel jobs. Agent decisions are logged at{" "}
              <code className="font-mono bg-background-deep border border-border-subtle px-1.5 py-0.5 rounded text-primary">GET /api/agent/decisions</code>.
            </p>
            <Link to="/app/search" className="text-xs font-semibold text-primary hover:underline inline-flex items-center gap-1">Open Search App →</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
