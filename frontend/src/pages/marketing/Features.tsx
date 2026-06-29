import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { 
  Search, 
  Shield, 
  Cpu, 
  Layers, 
  GitBranch, 
  Radio, 
  ArrowRight, 
  CheckCircle2, 
  Globe, 
  Shuffle, 
  Award, 
  Activity, 
  ChevronRight, 
  Terminal, 
  FileText, 
  Database,
  Building,
  Briefcase,
  GraduationCap,
  Scale
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

export function Features() {
  // Stepper for active pipeline visualizer
  const [activeStep, setActiveStep] = useState(0);
  
  // Community selector to show document solutions
  const [activeCommunity, setActiveCommunity] = useState("rag");

  const pipelineSteps = [
    {
      title: "Discover Widely",
      tagline: "Multisource Inbound Aggregation",
      tech: "SearchXNG, Wikidata, GDELT, OpenAlex, arXiv, Internet Archive",
      desc: "Queries are automatically parallelized across paid and free-first open web indices to fully capture all possible sources of truth.",
      status: "Aggregating indices in real-time..."
    },
    {
      title: "Crawl Safely & Ingest",
      tagline: "Secure Sandboxed Data Crawling",
      tech: "Playwright, Scrapy, SPF/MIME Validators, Sandbox Container Proxies",
      desc: "Dynamic web pages are rendered inside isolated, sandboxed Docker micro-containers with active SSRF defense and crawling rate limits.",
      status: "Sanitizing DOM payload..."
    },
    {
      title: "Normalize & Deduplicate",
      tagline: "Canonical Intelligence Alignment",
      tech: "Deduplication algorithms, Canonical naming, Entity extraction",
      desc: "Raw, redundant data is normalized. Similar text nodes, syndicated news, and author duplicates are extracted, parsed, and merged.",
      status: "Clustering duplicated claims..."
    },
    {
      title: "Aggressive Scoring & AI Validation",
      tagline: "Source Provenance Grounding",
      tech: "AI Critic Agents, Fact-Scoring Model, Peer networks cross-checking",
      desc: "Every claim undergoes rigorous algorithmic confidence scoring. Peer citations are mapped, retractions flagged, and trust scores weighted.",
      status: "Executing multi-agent review..."
    },
    {
      title: "Index Trusted Data",
      tagline: "Searchable Semantic Provenance Graph",
      tech: "Drizzle Schema, Postgres store, Vectors, Structured metadata exports",
      desc: "Cleaned and verified claiming structures are indexed as ready-to-run collections, fully transparent, auditable, and trace-backed.",
      status: "Verified output ready."
    }
  ];

  const communities = {
    rag: {
      title: "AI & RAG Engineering Teams",
      icon: Cpu,
      problem: "RAG systems fail when downstream source documents are stale, duplicated, badly extracted, or untrusted.",
      howHelps: "Produces clean, chunkable, source-traceable, and quality-scored documents designed for intelligent retrieval engines.",
      output: "RAG-ready datasets, raw markdown chunks with source citations, metadata JSON, and source confidence scores.",
      whyItMatters: "Gives AI systems clean context instead of feeding them untrustworthy internet compost."
    },
    osint: {
      title: "OSINT Researchers",
      icon: Search,
      problem: "Need to trace complex public facts, map entities, archived web pages, sudden events, and source relations safely.",
      howHelps: "Combines aggregate live search with safe proxy crawling, entity resolution nodes, and evidence tracking pipelines.",
      output: "Traceable investigation timelines, relationship maps, entity graph nodes, and cryptographic evidence bundles.",
      whyItMatters: "Turns fragmented public rumors into cohesive, defensible proof at rapid velocity."
    },
    academic: {
      title: "Academic & R&D Teams",
      icon: GraduationCap,
      problem: "Scholarly publications are heavily fragmented across arXiv, OpenAlex, Crossref, and diverse publisher pages.",
      howHelps: "Aggregates academic metadata metadata, detects conflicting citations, indexes preprints, and isolates author networks.",
      output: "Paper evidence cards, automated citation trails, comprehensive author profiles, and metadata conflict reports.",
      whyItMatters: "Improves technical literature discovery and simplifies high-stakes scientific validation."
    },
    compliance: {
      title: "Compliance & Risk Teams",
      icon: Scale,
      problem: "Requires constant, reliable tracking of regulatory updates, public notices, vendor risks, and policy-sensitive changes.",
      howHelps: "Establishes automated background monitors with continuous trace records, policy checks, and clear severity levels.",
      output: "Compliance review dashboards, secure email alerts, and cryptographically signed audit logs.",
      whyItMatters: "Eliminates regulatory blind spots and establishes defensible decision histories."
    },
    market: {
      title: "Market & Competitive Intelligence",
      icon: Briefcase,
      problem: "Competitive updates are spread across noisy blog posts, hiring pages, competitor disclosures, and social media channels.",
      howHelps: "Gathers scattered competitor and audience signals, filters duplicates, normalizes entity claims, and calculates reliability.",
      output: "Landscape dynamic brief, competitor product update tracker, and clean source-backed research collections.",
      whyItMatters: "Cuts out manual noise scanning and lets GTM/strategists react immediately to verified market shifts."
    }
  };

  const coreCapabilities = [
    {
      icon: Globe,
      title: "Multisource Inbound Aggregation",
      description: "Amalgamate unstructured evidence across academic databases, global news archives, maritime records, and public registries."
    },
    {
      icon: Shield,
      title: "Crawl Policy Control & Isolation",
      description: "Safely execute crawl pipelines through secure proxy proxies with automatic rate limiting and protection against server-side request forgery (SSRF)."
    },
    {
      icon: Shuffle,
      title: "Strict Duplication Removal",
      description: "Cluster identical assertions, syndicated articles, and redundant data structures instantly before committing content to your workspace."
    },
    {
      icon: Award,
      title: "Dynamic Provenance Scoring",
      description: "Every assertion receives a math-backed reliability score from 0 to 100 based on corroborating sources, historical reputation, and corrections."
    },
    {
      icon: Layers,
      title: "Interactive Evidence Trees",
      description: "Trace every summary point back to its underlying text fragment. Visual graphs expose exactly how claims are constructed."
    },
    {
      icon: Activity,
      title: "Automated Continuous Monitors",
      description: "Specify critical facts or metrics to monitor, and let background crawler systems automatically refresh and score new assertions daily."
    }
  ];

  // Motion animation parameters
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } }
  };

  return (
    <div className="bg-bg-deep pb-32 min-h-screen text-text-body">
      {/* Intro Hero Section */}
      <section className="relative overflow-hidden pt-32 pb-16 bg-bg-deep">
        <div className="absolute inset-0 bg-[url('https://transparenttextures.com/patterns/cubes.png')] opacity-[0.02] pointer-events-none mix-blend-multiply"></div>
        <div className="container mx-auto px-12 relative z-10 text-center max-w-4xl">
          <motion.div 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center border border-border-subtle bg-bg-surface px-3 py-1 text-[10px] uppercase tracking-widest font-medium text-text-body mb-6"
          >
            <span className="flex h-2 w-2 bg-text-subtle mr-2 animate-pulse"></span>
            Proven Grounding System Architecture
          </motion.div>
          
          <motion.h1 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-5xl md:text-[76px] font-serif italic text-text-title tracking-tight leading-[0.9] mb-8"
          >
            Core Capabilities &amp;<br />
            <span className="text-text-subtle">Engine Specifications</span>
          </motion.h1>
          
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-sm tracking-wide text-text-body max-w-2xl mx-auto leading-relaxed border-l border-border-subtle pl-6 text-left"
          >
            Unlike typical LLM systems that generate guesses and hallucinate claims, CredenceAI is engineered directly to crawlers, validation engines, and trust modeling algorithms in a mathematically traceable framework.
          </motion.p>
        </div>
      </section>

      {/* CORE CAPABILITIES BENTO GRID WITH MOTION */}
      <section className="py-16 bg-bg-deep">
        <div className="container mx-auto px-12 max-w-6xl">
          <div className="mb-12">
            <h2 className="text-xs uppercase tracking-[0.3em] font-bold text-text-title mb-3">Architectural Highlights</h2>
            <div className="h-px w-24 bg-border-accent"></div>
          </div>

          <motion.div 
            variants={containerVariants}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-100px" }}
            className="grid md:grid-cols-2 lg:grid-cols-3 gap-8"
          >
            {coreCapabilities.map((cap, i) => (
              <motion.div 
                key={i}
                variants={itemVariants}
                whileHover={{ y: -6, borderColor: "var(--border-accent)" }}
                className="p-8 border border-border-subtle bg-bg-surface transition-all duration-300 flex flex-col justify-between group"
              >
                <div>
                  <div className="h-12 w-12 border border-border-subtle flex items-center justify-center bg-bg-deep group-hover:bg-bg-panel transition-colors duration-300 text-text-title mb-6 rounded-none">
                    <cap.icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-xl font-serif italic text-text-title mb-3">{cap.title}</h3>
                  <p className="text-xs text-text-subtle leading-relaxed font-sans">{cap.description}</p>
                </div>
                <div className="mt-8 pt-4 border-t border-border-subtle/40 flex items-center text-[10px] uppercase font-bold tracking-widest text-[#10b981] opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  Engine Verified <CheckCircle2 className="h-3.5 w-3.5 ml-1.5" />
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* INTERACTIVE PIPELINE VISUALIZER */}
      <section className="py-20 bg-bg-surface border-y border-border-subtle">
        <div className="container mx-auto px-12 max-w-6xl">
          <div className="text-center mb-16">
            <span className="text-[10px] uppercase tracking-widest text-text-subtle font-bold bg-bg-deep px-3 py-1 border border-border-subtle inline-block mb-3">Operating Sequence</span>
            <h2 className="text-3xl md:text-4xl font-serif italic text-text-title">How CredenceAI processes a query</h2>
            <p className="text-xs text-text-subtle uppercase tracking-widest font-mono mt-3">From raw unstructured web data to clean cryptographically grounded intelligence</p>
          </div>

          <div className="grid lg:grid-cols-12 gap-12 items-start">
            {/* Interactive Steps List */}
            <div className="lg:col-span-5 space-y-4">
              {pipelineSteps.map((step, index) => (
                <button
                  key={index}
                  onClick={() => setActiveStep(index)}
                  className={`w-full text-left p-6 border transition-all duration-300 flex items-start gap-4 cursor-pointer outline-none ${
                    activeStep === index 
                      ? "bg-bg-deep border-border-accent shadow-lg" 
                      : "bg-transparent border-border-subtle hover:border-border-accent/50"
                  }`}
                >
                  <div className={`h-8 w-8 font-mono text-xs flex items-center justify-center border shrink-0 font-bold ${
                    activeStep === index ? "bg-text-title text-bg-deep border-text-title" : "border-border-subtle text-text-subtle"
                  }`}>
                    0{index + 1}
                  </div>
                  <div>
                    <h4 className={`text-sm font-semibold uppercase tracking-wider ${activeStep === index ? "text-text-title" : "text-text-subtle"}`}>
                      {step.title}
                    </h4>
                    <p className="text-[10px] text-text-subtle uppercase tracking-widest mt-1">{step.tagline}</p>
                  </div>
                  <ChevronRight className={`h-4 w-4 ml-auto self-center transition-transform duration-300 ${
                    activeStep === index ? "rotate-90 text-text-title" : "text-border-subtle"
                  }`} />
                </button>
              ))}
            </div>

            {/* Simulated Terminal Process Output */}
            <div className="lg:col-span-7 border border-border-subtle bg-bg-deep p-6 relative">
              <div className="flex items-center justify-between border-b border-border-subtle pb-4 mb-6">
                <div className="flex gap-1.5">
                  <span className="h-2.5 w-2.5 bg-red-500 rounded-full"></span>
                  <span className="h-2.5 w-2.5 bg-amber-500 rounded-full"></span>
                  <span className="h-2.5 w-2.5 bg-green-500 rounded-full"></span>
                </div>
                <div className="text-[9px] font-mono uppercase text-text-subtle tracking-widest">
                  System Pipeline Monitor
                </div>
              </div>

              <AnimatePresence mode="wait">
                <motion.div
                  key={activeStep}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-6"
                >
                  <div>
                    <span className="text-[9px] font-mono text-emerald-500 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 uppercase font-bold tracking-widest">
                      Step 0{activeStep + 1} Active
                    </span>
                    <h3 className="text-2xl font-serif italic text-text-title mt-3 font-semibold">
                      {pipelineSteps[activeStep].title}
                    </h3>
                    <p className="text-xs text-text-subtle uppercase tracking-widest font-mono mt-1">
                      {pipelineSteps[activeStep].tagline}
                    </p>
                  </div>

                  <p className="text-sm font-light text-text-body leading-relaxed border-l-2 border-border-subtle pl-4">
                    {pipelineSteps[activeStep].desc}
                  </p>

                  <div className="p-4 bg-bg-surface border border-border-subtle rounded-none space-y-3 font-mono text-xs">
                    <div className="text-text-subtle uppercase tracking-wider text-[9px] font-semibold border-b border-border-subtle/50 pb-1.5 flex items-center justify-between">
                      <span>Technological Architecture Stack</span>
                      <Terminal className="h-3 w-3" />
                    </div>
                    <div className="text-text-title font-medium leading-relaxed">
                      {pipelineSteps[activeStep].tech}
                    </div>
                  </div>

                  <div className="flex items-center gap-3 text-xs bg-bg-surface/50 border border-border-subtle/60 px-4 py-3">
                    <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse shrink-0"></span>
                    <span className="text-[10px] uppercase font-bold tracking-widest text-[#10b981] font-mono">
                      {pipelineSteps[activeStep].status}
                    </span>
                  </div>
                </motion.div>
              </AnimatePresence>
            </div>
          </div>
        </div>
      </section>

      {/* TARGET AUDIENCE RESOLUTION SECTION (FROM DOCUMENT TABLES) */}
      <section className="py-24 bg-bg-deep border-b border-border-subtle">
        <div className="container mx-auto px-12 max-w-6xl">
          <div className="max-w-3xl mb-16">
            <span className="text-[10px] uppercase tracking-widest text-text-subtle font-bold block mb-3">Enterprise Audience Tuning</span>
            <h2 className="text-4xl font-serif italic tracking-tight text-text-title mb-4">
              Spec-Tuned For High-Stakes Investigators
            </h2>
            <p className="text-xs uppercase tracking-widest text-text-subtle font-medium border-l border-border-subtle pl-4 leading-relaxed mt-2">
              Our core grounding pipeline maps perfectly to specific compliance, RAG database, academic, and analytical demands outlined in the CredenceAI product design guidelines.
            </p>
          </div>

          {/* Interactive Audience Tabs */}
          <div className="flex flex-wrap border-b border-border-subtle mb-10 gap-2">
            {Object.entries(communities).map(([key, value]) => {
              const Icon = value.icon;
              return (
                <button
                  key={key}
                  onClick={() => setActiveCommunity(key)}
                  className={`px-5 py-3.5 text-xs uppercase tracking-widest font-bold border-b-2 transition-all cursor-pointer flex items-center gap-2 ${
                    activeCommunity === key 
                      ? "border-text-title text-text-title font-semibold" 
                      : "border-transparent text-text-subtle hover:text-text-title"
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span>{value.title.split(" & ")[0].split(" Teams")[0]}</span>
                </button>
              );
            })}
          </div>

          {/* Audience Specific Content Card */}
          <div className="border border-border-subtle bg-bg-surface overflow-hidden">
            <div className="h-10 border-b border-border-subtle px-6 flex items-center justify-between bg-bg-panel text-text-subtle text-[10px] uppercase font-mono tracking-widest">
              <span>Audience Guideline Target Card</span>
              <FileText className="h-3 w-3" />
            </div>
            
            <AnimatePresence mode="wait">
              <motion.div
                key={activeCommunity}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.3 }}
                className="p-10 grid md:grid-cols-2 gap-12"
              >
                <div className="space-y-6">
                  <div>
                    <h3 className="text-2xl font-serif italic text-text-title font-semibold flex items-center gap-2">
                      {communities[activeCommunity as keyof typeof communities].title}
                    </h3>
                  </div>

                  <div className="space-y-2">
                    <span className="text-[9px] uppercase tracking-widest font-bold text-red-500 block">Critical Workspace Pain-Point</span>
                    <p className="text-sm text-text-body leading-relaxed border-l-2 border-red-500/50 pl-4 bg-red-500/5 py-2">
                      {communities[activeCommunity as keyof typeof communities].problem}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <span className="text-[9px] uppercase tracking-widest font-bold text-emerald-500 block">How CredenceAI Resolves</span>
                    <p className="text-sm text-text-body leading-relaxed border-l-2 border-emerald-500/50 pl-4 bg-emerald-500/5 py-2">
                      {communities[activeCommunity as keyof typeof communities].howHelps}
                    </p>
                  </div>
                </div>

                <div className="flex flex-col justify-between border-t md:border-t-0 md:border-l border-border-subtle pt-8 md:pt-0 md:pl-10">
                  <div className="space-y-4">
                    <span className="text-[9px] uppercase tracking-widest font-bold text-text-title block">Verified Technical Payload Out</span>
                    <div className="p-5 bg-bg-deep border border-border-subtle border-dashed rounded-none">
                      <ul className="space-y-3.5">
                        {communities[activeCommunity as keyof typeof communities].output.split(", ").map((out, idx) => (
                          <li key={idx} className="flex items-start text-xs text-text-body font-mono">
                            <span className="mr-2 text-emerald-500 font-bold">&#10003;</span>
                            <span>{out}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="mt-8">
                    <span className="text-[9px] uppercase tracking-[0.2em] font-medium text-text-subtle block">Core Practical Importance</span>
                    <p className="text-xs text-text-title italic font-serif leading-relaxed mt-2 pl-4 border-l border-border-accent">
                      "{communities[activeCommunity as keyof typeof communities].whyItMatters}"
                    </p>
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </section>

      {/* INTERACTIVE DEVELOPMENT ITERATION TIMELINE (FROM PDF PAGE 5) */}
      <section className="py-24 bg-bg-surface border-b border-border-subtle">
        <div className="container mx-auto px-12 max-w-6xl">
          <div className="text-center mb-16">
            <span className="text-[10px] uppercase tracking-widest text-text-subtle font-bold bg-bg-deep px-3 py-1 border border-border-subtle inline-block mb-3">Evolution Timeline</span>
            <h2 className="text-3xl md:text-4xl font-serif italic text-text-title">Interactive Engine Roadmap</h2>
            <p className="text-xs text-text-subtle uppercase tracking-widest font-mono mt-3">The five continuous evolution milestones of the CredenceAI grounding pipeline</p>
          </div>

          <div className="grid md:grid-cols-5 gap-4 relative">
            {/* Horizontal Line behind icons */}
            <div className="hidden md:block absolute top-10 left-8 right-8 h-px bg-border-subtle/50 z-0"></div>

            {[
              {
                num: "I",
                phase: "Iteration 1",
                focus: "Core MVP Pipeline",
                improves: "Basic search & crawling",
                deliverable: "Searchable normalized results",
                status: "Released"
              },
              {
                num: "II",
                phase: "Iteration 2",
                focus: "Quality & Entity Linking",
                improves: "Mathematical accuracy & trust",
                deliverable: "Scored, duplicate-resolved, linked results",
                status: "Released"
              },
              {
                num: "III",
                phase: "Iteration 3",
                focus: "Safe Sandbox Crawling",
                improves: "Deep coverage & content extraction",
                deliverable: "Crawled, extracted, validated records",
                status: "Released"
              },
              {
                num: "IV",
                phase: "Iteration 4",
                focus: "Agentic Verification",
                improves: "Validation & intelligence maps",
                deliverable: "Evidence-backed multi-source panels",
                status: "Active Release"
              },
              {
                num: "V",
                phase: "Iteration 5",
                focus: "Scale & Benchmarks",
                improves: "Speed, latency, and throughput",
                deliverable: "Production-grade scalable system",
                status: "In Development"
              }
            ].map((stage, i) => (
              <div 
                key={i} 
                className="relative z-10 p-6 border border-border-subtle bg-bg-deep hover:border-border-accent transition-all group flex flex-col justify-between"
              >
                <div>
                  <div className="h-10 w-10 border border-border-subtle flex items-center justify-center font-mono text-xs font-bold bg-bg-surface text-text-title mb-4 z-10 relative">
                    {stage.num}
                  </div>
                  <div className="text-[9px] uppercase tracking-widest font-mono font-bold text-text-subtle mb-1">
                    {stage.phase}
                  </div>
                  <h4 className="text-sm font-serif italic text-text-title font-bold mb-2 leading-tight">
                    {stage.focus}
                  </h4>
                  <div className="text-[10px] text-text-subtle uppercase tracking-wider mb-4 font-sans leading-normal">
                    <span className="font-semibold text-text-body">Improves:</span> {stage.improves}
                  </div>
                </div>

                <div className="border-t border-border-subtle/40 pt-4 mt-2">
                  <div className="text-[10px] font-mono leading-relaxed text-text-body">
                    <span className="text-[9px] text-text-subtle font-bold uppercase block mb-1">Core Deliverable:</span>
                    {stage.deliverable}
                  </div>
                  <span className={`inline-block mt-3 px-2 py-0.5 text-[8px] uppercase tracking-widest font-mono font-bold border ${
                    stage.status === "Released" ? "text-emerald-500 bg-emerald-505/5 border-emerald-500/20" :
                    stage.status === "Active Release" ? "text-[#10b981] bg-emerald-505/10 border-emerald-500/30 font-extrabold animate-pulse" :
                    "text-amber-500 bg-amber-500/5 border-amber-500/20"
                  }`}>
                    {stage.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA FOOTER */}
      <section className="pt-20">
        <div className="container mx-auto px-12 max-w-6xl">
          <motion.div 
            initial={{ opacity: 0, scale: 0.98 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="p-12 border border-border-subtle bg-bg-surface flex flex-col md:flex-row md:items-center justify-between gap-8"
          >
            <div>
              <h3 className="text-3xl font-serif italic text-text-title mb-2">Ready to explore the intelligence engine?</h3>
              <p className="text-xs text-text-subtle font-mono uppercase tracking-widest leading-relaxed mt-1">Join forward-thinking enterprise research teams worldwide.</p>
            </div>
            <Button asChild size="lg" className="shrink-0 relative group">
              <Link to="/auth/sign-up" className="flex items-center">
                Start Free Trial 
                <ArrowRight className="h-4 w-4 ml-2 transition-transform duration-300 group-hover:translate-x-1" />
              </Link>
            </Button>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
