import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Search, ShieldCheck, Database, ArrowRight, ChevronRight } from "lucide-react";

export function Home() {
  return (
    <div className="flex-1 bg-bg-deep text-text-body">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-24 pb-32 lg:pt-36 bg-bg-deep">
        <div className="absolute inset-0 bg-[url('https://transparenttextures.com/patterns/cubes.png')] opacity-[0.03] pointer-events-none mix-blend-multiply"></div>
        <div className="container mx-auto px-12 relative z-10 text-center">
          <div className="inline-flex items-center border border-border-subtle bg-bg-panel px-3 py-1 text-[10px] uppercase tracking-widest font-medium text-text-body mb-8">
            <span className="flex h-2 w-2 bg-text-subtle mr-2 animate-pulse"></span>
            CredenceAI Enterprise 2.0 is now available
            <ChevronRight className="h-4 w-4 ml-1 inline text-text-subtle/60" />
          </div>
          <h1 className="text-6xl md:text-[84px] font-serif italic text-text-title max-w-4xl mx-auto mb-8 leading-[0.9]">
            Research intelligence <br className="hidden md:block"/><span className="text-text-subtle">you can verify.</span>
          </h1>
          <p className="text-sm tracking-wide text-text-body max-w-2xl mx-auto mb-10 font-sans border-l border-border-subtle pl-6 leading-relaxed text-left">
            Search, score, and operationalize information across web, news, and scholarly sources. Designed for analysts who demand complete provenance.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            <Button size="lg" asChild>
              <Link to="/auth/sign-up">Start Free</Link>
            </Button>
            <Button size="lg" variant="outline" className="border-border-subtle bg-btn-outline-bg hover:bg-bg-panel hover:text-text-title">
              <Link to="/enterprise">Book Demo</Link>
            </Button>
          </div>
        </div>

        {/* Product Preview Mockup */}
        <div className="container mx-auto mt-24 px-12 max-w-6xl relative z-20">
           <div className="border border-border-subtle bg-bg-surface shadow-2xl overflow-hidden">
              <div className="h-12 border-b border-border-subtle flex items-center px-6 gap-2 bg-bg-deep">
                 <div className="flex gap-1.5">
                    <div className="h-3 w-3 bg-text-subtle/30"></div>
                    <div className="h-3 w-3 bg-text-subtle/30"></div>
                    <div className="h-3 w-3 bg-text-subtle/30"></div>
                 </div>
                 <div className="mx-auto w-1/2 max-w-md h-7 border border-border-subtle bg-bg-surface flex items-center px-3 text-[10px] text-text-subtle font-mono tracking-widest uppercase">
                    <Search className="h-3 w-3 mr-2" />
                    Query: "Quantum computing material synthesis timelines"
                 </div>
              </div>
              <div className="flex grid-cols-12 h-[32rem]">
                 <div className="hidden md:block w-64 border-r border-border-subtle bg-bg-deep p-6 shrink-0">
                    <div className="h-4 w-24 bg-border-subtle mb-6"></div>
                    <div className="space-y-4">
                       <div className="h-8 bg-border-subtle/50"></div>
                       <div className="h-8 bg-bg-panel"></div>
                       <div className="h-8 bg-bg-panel"></div>
                    </div>
                 </div>
                 <div className="flex-1 p-10 bg-bg-surface overflow-hidden relative">
                    <div className="flex items-center justify-between mb-8">
                       <div>
                          <h3 className="text-3xl font-serif italic text-text-title mb-3">Entity Report: Quantum Silicon Corp.</h3>
                          <div className="flex gap-2">
                             <span className="px-2 py-0.5 bg-bg-panel text-text-body text-[10px] uppercase font-bold tracking-widest border border-border-subtle">Organization</span>
                             <span className="px-2 py-0.5 bg-bg-deep text-text-subtle text-[10px] uppercase font-bold tracking-widest border border-border-subtle">Material Science</span>
                          </div>
                       </div>
                       <div className="text-right">
                          <div className="text-[10px] text-text-subtle mb-2 uppercase tracking-[0.2em] font-medium">Trust Score</div>
                          <div className="text-4xl font-serif italic text-highlight-color font-bold">94/100</div>
                       </div>
                    </div>

                    <div className="space-y-4">
                       {[1, 2, 3].map((i) => (
                          <div key={i} className="p-6 border border-border-subtle bg-bg-surface hover:border-border-accent transition-colors">
                             <div className="flex items-start justify-between mb-4">
                                <div className="text-sm font-medium text-text-body pr-4 leading-relaxed">Breakthrough reported in silicon spin qubit fidelity at 99.9%</div>
                                <div className="shrink-0 flex items-center text-[10px] uppercase tracking-widest font-semibold text-highlight-color bg-highlight-color/10 border border-highlight-color/20 px-2 py-1">
                                   <ShieldCheck className="h-3 w-3 mr-1" /> High Confidence
                                </div>
                             </div>
                             <div className="flex items-center justify-between text-xs text-text-subtle">
                                <div className="flex items-center gap-2 uppercase tracking-wider text-[10px]">
                                   <span className="w-1.5 h-1.5 bg-text-subtle/55"></span> Nature Physics Journal &bull; Oct 2024
                                </div>
                                <a href="#" className="hover:text-text-title flex items-center uppercase tracking-widest text-[10px] font-semibold">View Evidence <ArrowRight className="h-3 w-3 ml-1" /></a>
                             </div>
                          </div>
                       ))}
                    </div>
                 </div>
              </div>
           </div>
        </div>
      </section>

      {/* Value Props */}
      <section className="py-32 bg-bg-surface border-t border-border-subtle">
         <div className="container mx-auto px-12 max-w-7xl">
            <div className="text-center mb-24 max-w-3xl mx-auto">
               <h2 className="text-4xl md:text-5xl font-serif italic text-text-title mb-6">Intelligence built for high-stakes environments.</h2>
               <p className="text-sm tracking-wide text-text-subtle leading-relaxed">Generic AI hallucinates. CredenceAI maps the provenance graph of every assertion back to verifiable sources.</p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-12">
               <div className="p-8 border border-border-subtle bg-bg-deep">
                  <div className="h-12 w-12 border border-border-subtle bg-bg-surface flex items-center justify-center mb-8">
                     <Search className="h-5 w-5 text-text-title" />
                  </div>
                  <h3 className="text-lg font-serif italic text-text-title mb-4">Deep Source Search</h3>
                  <p className="text-text-body text-sm leading-relaxed">Query across academic journals, regulatory filings, dark web archives, and global news instantly.</p>
               </div>
               <div className="p-8 border border-border-subtle bg-bg-deep">
                  <div className="h-12 w-12 border border-border-subtle bg-bg-surface flex items-center justify-center mb-8">
                     <ShieldCheck className="h-5 w-5 text-text-title" />
                  </div>
                  <h3 className="text-lg font-serif italic text-text-title mb-4">Verifiable Scoring</h3>
                  <p className="text-text-body text-sm leading-relaxed">Every claim includes a dynamic trust score generated by checking cross-source corroboration and author history.</p>
               </div>
               <div className="p-8 border border-border-subtle bg-bg-deep">
                  <div className="h-12 w-12 border border-border-subtle bg-bg-surface flex items-center justify-center mb-8">
                     <Database className="h-5 w-5 text-text-title" />
                  </div>
                  <h3 className="text-lg font-serif italic text-text-title mb-4">API & Integration</h3>
                  <p className="text-text-body text-sm leading-relaxed">Export findings instantly to JSON/CSV or pipe real-time intelligence directly into your existing dashboard.</p>
               </div>
            </div>

            {/* CredenceAI vs Traditional Solutions Section (from PDF PAGE 1) */}
            <div className="mt-32 pt-20 border-t border-border-subtle/60">
               <div className="text-center mb-16 max-w-2xl mx-auto">
                  <span className="text-[10px] uppercase tracking-widest text-[#10b981] font-bold bg-[#10b981]/10 border border-[#10b981]/20 px-3 py-1 inline-block mb-3">Architectural Comparison</span>
                  <h2 className="text-3xl md:text-4xl font-serif italic text-text-title">What separates CredenceAI from legacy tools?</h2>
                  <p className="text-xs text-text-subtle uppercase tracking-widest font-mono mt-2">A direct analysis of structural limits vs. the CredenceAI solution framework</p>
               </div>

               <div className="border border-border-subtle overflow-x-auto bg-bg-deep">
                  <table className="w-full text-left border-collapse min-w-[800px]">
                     <thead>
                        <tr className="border-b border-border-subtle bg-bg-panel/70">
                           <th className="p-5 text-[10px] uppercase tracking-widest font-bold text-text-title">Current Solution Type</th>
                           <th className="p-5 text-[10px] uppercase tracking-widest font-bold text-text-title">What It Does</th>
                           <th className="p-5 text-[10px] uppercase tracking-widest font-bold text-text-title">Limitation</th>
                           <th className="p-5 text-[10px] uppercase tracking-widest font-bold text-[#10b981]">CredenceAI Advantage</th>
                        </tr>
                     </thead>
                     <tbody className="divide-y divide-border-subtle bg-bg-surface">
                        <tr className="hover:bg-bg-panel/20 transition-colors">
                           <td className="p-5 font-mono text-xs font-semibold text-text-title">SERP APIs</td>
                           <td className="p-5 text-xs text-text-body">Return search results</td>
                           <td className="p-5 text-xs text-text-subtle">Costly, vendor-dependent, not trust-aware</td>
                           <td className="p-5 text-xs font-medium text-[#10b981]">Free-first, scored, deduplicated, validated</td>
                        </tr>
                        <tr className="hover:bg-bg-panel/20 transition-colors">
                           <td className="p-5 font-mono text-xs font-semibold text-text-title">Crawlers</td>
                           <td className="p-5 text-xs text-text-body">Collect web pages</td>
                           <td className="p-5 text-xs text-text-subtle">Unsafe/noisy without policy and scoring</td>
                           <td className="p-5 text-xs font-medium text-[#10b981]">Safe selective crawling with validation</td>
                        </tr>
                        <tr className="hover:bg-bg-panel/20 transition-colors">
                           <td className="p-5 font-mono text-xs font-semibold text-text-title">Search Indexes</td>
                           <td className="p-5 text-xs text-text-body">Retrieve stored data</td>
                           <td className="p-5 text-xs text-text-subtle">Need clean input data to prevent feedback loops</td>
                           <td className="p-5 text-xs font-medium text-[#10b981]">Prepares and models trusted indexed data</td>
                        </tr>
                        <tr className="hover:bg-bg-panel/20 transition-colors">
                           <td className="p-5 font-mono text-xs font-semibold text-text-title">Vector Databases</td>
                           <td className="p-5 text-xs text-text-body">Semantic retrieval</td>
                           <td className="p-5 text-xs text-text-subtle">Can retrieve bad or stale context chunks</td>
                           <td className="p-5 text-xs font-medium text-[#10b981]">Quality-scored, source-traceable chunks</td>
                        </tr>
                        <tr className="hover:bg-bg-panel/20 transition-colors">
                           <td className="p-5 font-mono text-xs font-semibold text-text-title">AI Search Tools</td>
                           <td className="p-5 text-xs text-text-body">Search and summarize web content</td>
                           <td className="p-5 text-xs text-text-subtle">Often less auditable, prone to synthesis hallucination</td>
                           <td className="p-5 text-xs font-medium text-[#10b981]">Evidence-backed, governed intelligence pipeline</td>
                        </tr>
                        <tr className="hover:bg-bg-panel/20 transition-colors">
                           <td className="p-5 font-mono text-xs font-semibold text-text-title">Research APIs</td>
                           <td className="p-5 text-xs text-text-body">Provide scholarly metadata</td>
                           <td className="p-5 text-xs text-text-subtle">Fragmented and highly source-specific</td>
                           <td className="p-5 text-xs font-medium text-[#10b981]">Unified scholarly intelligence with conflict handling</td>
                        </tr>
                     </tbody>
                  </table>
               </div>
            </div>
         </div>
      </section>
    </div>
  );
}
