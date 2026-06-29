import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

export function Pricing() {
  const tiers = [
    {
      name: "Free",
      description: "For individuals exploring the platform.",
      price: "$0",
      period: "/month",
      audience: "Individuals",
      features: ["50 public searches/day", "Basic result cards", "Limited provenance depth", "Community support"],
      notIncluded: ["Export to CSV/JSON", "Saved Collections", "API Access", "Team Collaboration"],
      cta: "Start Free",
      href: "/auth/sign-up",
      highlight: false,
    },
    {
      name: "Pro",
      description: "For independent researchers and analysts.",
      price: "$49",
      period: "/month",
      audience: "Professionals",
      features: ["500 searches/day", "Full evidence panels", "Saved collections & workspaces", "Export to CSV/JSON", "Basic monitors", "Email support"],
      notIncluded: ["Team Collaboration", "Advanced Audit Logs"],
      cta: "Upgrade to Pro",
      href: "/auth/sign-in",
      highlight: true,
    },
    {
      name: "Team",
      description: "For small teams and research groups.",
      price: "$149",
      period: "/user/month",
      audience: "Small Teams",
      features: ["Unlimited searches", "Shared collections", "Team dashboard & review", "1,000 API credits/mo", "Priority support"],
      notIncluded: ["SSO/SAML", "Custom Data Retention"],
      cta: "Start Team Trial",
      href: "/auth/sign-in",
      highlight: false,
    },
    {
      name: "Enterprise",
      description: "For large orgs and regulated environments.",
      price: "Custom",
      period: "",
      audience: "Enterprises",
      features: ["SSO / SAML", "Custom data retention", "Advanced audit logs", "Private deployment options", "Dedicated success manager"],
      notIncluded: [],
      cta: "Contact Sales",
      href: "#",
      highlight: false,
    }
  ];

  return (
    <div className="bg-bg-deep pb-32 min-h-screen text-text-body">
      {/* Header */}
      <div className="pt-32 pb-24 text-center px-12 max-w-3xl mx-auto">
         <h1 className="text-5xl md:text-6xl font-serif italic mb-8 text-text-title tracking-tight">Simple, transparent pricing</h1>
         <p className="text-sm tracking-wide text-text-subtle font-sans border-l border-border-subtle pl-6 leading-relaxed max-w-xl mx-auto text-left">
           Whether you're an independent investigator or a global intelligence team, we have a plan designed to scale with your research needs.
         </p>
      </div>

      {/* Pricing Cards */}
      <div className="container mx-auto px-12 max-w-7xl">
         <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {tiers.map((tier) => (
               <div 
                 key={tier.name}
                 className={cn(
                   "border flex flex-col bg-bg-surface p-10 transition-colors duration-300",
                   tier.highlight ? "border-border-accent relative" : "border-border-subtle"
                 )}
               >
                  {tier.highlight && (
                     <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-accent text-accent-foreground border border-border-accent text-[10px] font-bold px-4 py-2 uppercase tracking-[0.2em]">
                        Most Popular
                     </div>
                  )}
                  <div className="mb-8">
                     <h3 className="font-serif italic text-2xl text-text-title mb-4">{tier.name}</h3>
                     <p className="text-xs text-text-subtle tracking-wide h-10">{tier.description}</p>
                  </div>
                  <div className="mb-8 flex items-baseline text-5xl font-serif text-text-title">
                     {tier.price}
                     <span className="text-[10px] uppercase tracking-widest text-text-subtle ml-2">{tier.period}</span>
                  </div>
                  <Button 
                    asChild 
                    variant={tier.highlight ? "default" : "outline"}
                    className="mb-8 w-full border-border-subtle"
                  >
                     <Link to={tier.href}>{tier.cta}</Link>
                  </Button>
                  <div className="space-y-6 flex-1">
                     <div className="text-[10px] uppercase tracking-[0.2em] font-medium text-text-subtle border-b border-border-subtle pb-2">Included</div>
                     <ul className="space-y-4">
                        {tier.features.map((feature, i) => (
                           <li key={i} className="flex items-start text-xs text-text-body">
                              <CheckCircle2 className="h-3 w-3 text-text-subtle shrink-0 mr-3 mt-0.5" />
                              <span>{feature}</span>
                           </li>
                        ))}
                     </ul>
                  </div>
               </div>
            ))}
         </div>
      </div>
    </div>
  );
}
