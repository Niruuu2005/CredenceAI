import { Outlet, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Activity } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";

export function MarketingLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-bg-deep text-text-body">
      <header className="sticky top-0 z-50 w-full border-b border-border-subtle bg-header-footer">
        <div className="container mx-auto px-12 flex h-24 items-center justify-between">
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 border border-text-subtle flex items-center justify-center rotate-45">
              <span className="-rotate-45 text-xs font-bold tracking-widest text-text-title">C</span>
            </div>
            <span className="text-sm tracking-[0.4em] uppercase font-light text-logo-text-color ml-2">CredenceAI</span>
          </Link>
          <nav className="hidden md:flex items-center space-x-10 text-[11px] uppercase tracking-[0.2em] font-medium text-text-subtle">
            <Link to="/features" className="hover:text-text-title transition-colors">Features</Link>
            <Link to="/pricing" className="hover:text-text-title transition-colors">Pricing</Link>
            <Link to="/docs" className="hover:text-text-title transition-colors">Docs</Link>
            <Link to="/enterprise" className="hover:text-text-title transition-colors">Enterprise</Link>
          </nav>
          <div className="flex items-center space-x-6">
            <Link to="/auth/sign-in" className="text-[11px] uppercase tracking-[0.2em] font-medium text-text-subtle hover:text-text-title hidden sm:inline-block">Sign In</Link>
            <Button asChild size="sm">
              <Link to="/auth/sign-up">Start Free</Link>
            </Button>
            <ThemeToggle />
          </div>
        </div>
      </header>
      <main className="flex-1 flex flex-col bg-bg-deep">
        <Outlet />
      </main>
      <footer className="border-t border-border-subtle py-16 bg-header-footer">
        <div className="container mx-auto px-12 grid grid-cols-2 md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center space-x-2 mb-6">
              <div className="w-6 h-6 border border-text-subtle flex items-center justify-center rotate-45">
                <span className="-rotate-45 text-[10px] font-bold tracking-widest text-text-title">C</span>
              </div>
              <span className="text-xs tracking-[0.3em] uppercase font-light text-logo-text-color ml-2">Credence</span>
            </div>
            <p className="text-xs text-text-subtle leading-relaxed">Trust-first intelligence <br/>for rigorous research.</p>
          </div>
          <div>
            <h4 className="text-[10px] uppercase tracking-[0.2em] font-medium text-text-title mb-6">Product</h4>
            <ul className="space-y-4 text-xs text-text-subtle">
              <li><Link to="/features" className="hover:text-text-title transition-colors">Search Intelligence</Link></li>
              <li><Link to="/features" className="hover:text-text-title transition-colors">Monitors & Alerts</Link></li>
              <li><Link to="/pricing" className="hover:text-text-title transition-colors">Pricing</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-[10px] uppercase tracking-[0.2em] font-medium text-text-title mb-6">Company</h4>
            <ul className="space-y-4 text-xs text-text-subtle">
              <li><Link to="/enterprise" className="hover:text-text-title transition-colors">About</Link></li>
              <li><Link to="/enterprise" className="hover:text-text-title transition-colors">Customers</Link></li>
              <li><Link to="/enterprise" className="hover:text-text-title transition-colors">Careers</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-[10px] uppercase tracking-[0.2em] font-medium text-text-title mb-6">Legal</h4>
            <ul className="space-y-4 text-xs text-text-subtle">
              <li><Link to="/legal?tab=privacy" className="hover:text-text-title transition-colors">Privacy</Link></li>
              <li><Link to="/legal?tab=terms" className="hover:text-text-title transition-colors">Terms</Link></li>
              <li><Link to="/legal?tab=security" className="hover:text-text-title transition-colors">Security</Link></li>
            </ul>
          </div>
        </div>
      </footer>
    </div>
  );
}
