import { useState, useEffect } from "react";
import { Outlet, Link, useLocation } from "react-router-dom";
import { LayoutDashboard, Search, Database, Bell, Settings, CreditCard, Menu, X, LogOut, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/ThemeToggle";
import { api } from "@/lib/api";
import { withWakeupRetry } from "@/lib/retry";

type LayoutUser = {
  name: string;
  email: string;
  picture: string | null;
  plan?: string;
  search_quota_limit?: number;
  search_used?: number;
};

export function AppLayout() {
  const location = useLocation();
  const path = location.pathname;

  const [searchUsed, setSearchUsed] = useState(0);
  const [user, setUser] = useState<LayoutUser | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const fetchUser = async (): Promise<boolean> => {
    try {
      const u = await withWakeupRetry(() => api.getCurrentUser());
      setUser(u);
      setSearchUsed(u.search_used ?? 0);
      return true;
    } catch (err) {
      console.error("Failed to load user profile in layout:", err);
      return false;
    }
  };

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    let cancelled = false;
    let intervalMs = 30000;

    const tick = async () => {
      if (cancelled) return;
      const userOk = await fetchUser();
      intervalMs = userOk ? 30000 : Math.min(120000, intervalMs * 2);
      if (!cancelled) {
        timer = setTimeout(tick, intervalMs);
      }
    };

    tick();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, []);

  // Close mobile sidebar on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [path]);

  const navItems = [
    { name: "Research", href: "/app/research", icon: Sparkles },
    { name: "Dashboard", href: "/app/dashboard", icon: LayoutDashboard },
    { name: "Search", href: "/app/search", icon: Search },
    { name: "Collections", href: "/app/collections", icon: Database },
    { name: "Monitors", href: "/app/monitors", icon: Bell },
  ];

  const bottomItems = [
    { name: "Settings", href: "/app/settings", icon: Settings },
    { name: "Billing", href: "/app/billing", icon: CreditCard },
  ];

  const quotaLimit = user?.search_quota_limit || 50;

  const SidebarContent = () => (
    <div className="flex flex-col h-full bg-background-surface/90 backdrop-blur-xl select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-border-subtle shrink-0">
        <Link to="/app/research" className="flex items-center space-x-3 group">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-400 text-black flex items-center justify-center font-sans font-extrabold text-sm shadow-[0_0_15px_rgba(16,185,129,0.3)] transition-transform group-hover:scale-105">
            C
          </div>
          <div className="flex flex-col">
            <span className="font-sans font-bold text-sm text-text-title tracking-tight leading-none group-hover:text-primary transition-colors">CredenceAI</span>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="text-[11px] font-medium text-text-subtle">Intelligence Hub</span>
            </div>
          </div>
        </Link>
      </div>
      
      {/* Nav Links */}
      <div className="p-3.5 flex flex-col flex-1 gap-1 overflow-y-auto">
        <div className="text-xs font-semibold text-text-subtle/80 px-2.5 py-1 mb-1">Platform</div>
        {navItems.map((item) => {
          const isActive = path === item.href;
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                "flex items-center space-x-3 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-200",
                isActive 
                  ? "bg-primary/10 text-primary border border-primary/25 font-semibold shadow-[0_0_15px_rgba(16,185,129,0.1)]" 
                  : "text-text-subtle hover:bg-background-panel hover:text-text-title border border-transparent"
              )}
            >
              <item.icon className={cn("h-4 w-4 shrink-0 transition-colors", isActive ? "text-primary" : "text-text-subtle")} />
              <span>{item.name}</span>
            </Link>
          );
        })}
        
        {/* Quota Section */}
        <div className="mt-6 text-xs font-semibold text-text-subtle/80 px-2.5 mb-2">Usage & Limits</div>
        <div className="p-3.5 rounded-xl bg-background-deep border border-border-subtle space-y-2.5 mx-1">
           <div className="flex justify-between text-xs">
              <span className="text-text-subtle font-medium">Daily Queries ({user?.plan || "Free"})</span>
              <span className="font-mono text-text-title font-semibold">{searchUsed}/{quotaLimit}</span>
           </div>
           <div className="h-1.5 w-full bg-background-panel rounded-full overflow-hidden">
              <div 
                 className="h-full bg-gradient-to-r from-emerald-500 to-cyan-400 rounded-full transition-all duration-500" 
                 style={{ width: `${Math.min(100, (searchUsed / quotaLimit) * 100)}%` }}
              />
           </div>
           <div className="flex items-center justify-between pt-1">
              <span className="text-[11px] text-text-subtle">Audit line verified</span>
              <Link to="/app/billing" className="text-[11px] text-primary font-semibold hover:underline">Upgrade</Link>
           </div>
        </div>
      </div>

      {/* User Info & Settings */}
      <div className="p-3.5 border-t border-border-subtle gap-1 flex flex-col shrink-0">
        {bottomItems.map((item) => {
          const isActive = path === item.href;
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                "flex items-center space-x-3 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-200",
                isActive 
                  ? "bg-primary/10 text-primary border border-primary/25 font-semibold shadow-[0_0_15px_rgba(16,185,129,0.1)]" 
                  : "text-text-subtle hover:bg-background-panel hover:text-text-title border border-transparent"
              )}
            >
              <item.icon className={cn("h-4 w-4 shrink-0", isActive ? "text-primary" : "text-text-subtle")} />
              <span>{item.name}</span>
            </Link>
          );
        })}
        
        {/* Profile Card */}
        <div className="mt-3 p-2.5 rounded-xl bg-background-deep border border-border-subtle flex items-center justify-between mx-1">
          <div className="flex items-center space-x-2.5 min-w-0">
             {user?.picture ? (
                <img src={user.picture} className="h-8 w-8 rounded-lg border border-border-subtle object-cover bg-background-panel" alt="Avatar" referrerPolicy="no-referrer" />
             ) : (
                <div className="h-8 w-8 rounded-lg border border-border-subtle bg-background-panel flex items-center justify-center text-text-title font-sans font-bold text-xs">
                   {user?.name ? user.name.split(' ').map((n: string) => n[0]).join('').toUpperCase() : (user?.email?.[0]?.toUpperCase() || '?')}
                </div>
             )}
             <div className="flex flex-col min-w-0">
                <span className="text-xs font-semibold text-text-title truncate max-w-[110px]" title={user?.name || user?.email || ""}>
                  {user?.name || user?.email || "Account"}
                </span>
                <span className="text-[10px] text-emerald-400 font-medium">{user?.plan || "Free"} Plan</span>
             </div>
          </div>
          <button 
             onClick={() => {
                api.logout();
                window.location.href = "/auth/sign-in";
             }}
             className="h-8 w-8 rounded-lg flex items-center justify-center text-text-subtle hover:text-red-400 bg-background-panel hover:bg-red-500/10 border border-border-subtle hover:border-red-500/20 active:scale-95 cursor-pointer transition-all"
             title="Sign Out"
          >
             <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen overflow-hidden bg-background text-text-body font-sans">
      {/* Desktop Sidebar (visible on screens >= 1024px) */}
      <aside className="hidden lg:flex w-64 bg-background-surface flex-col flex-shrink-0 h-full overflow-hidden border-r border-border-subtle z-30">
        <SidebarContent />
      </aside>

      {/* Mobile Drawer (visible on screens < 1024px) */}
      <div 
        className={cn(
          "fixed inset-0 z-50 bg-black/50 backdrop-blur-sm transition-opacity duration-300 lg:hidden",
          isMobileMenuOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        )}
        onClick={() => setIsMobileMenuOpen(false)}
      />
      <aside 
        className={cn(
          "fixed top-0 bottom-0 left-0 z-50 w-64 bg-background-surface flex flex-col h-full shadow-2xl transition-transform duration-300 ease-in-out lg:hidden",
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <SidebarContent />
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 h-full overflow-hidden bg-background relative">
         <header className="h-16 bg-background-surface/95 backdrop-blur-xl flex items-center px-6 shrink-0 justify-between z-40 border-b border-border-subtle sticky top-0">
            <div className="flex items-center space-x-3">
              {/* Hamburger Button for mobile */}
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="lg:hidden p-2 rounded-xl text-text-body hover:bg-background-panel active:scale-95 border border-border-subtle transition-all cursor-pointer"
                aria-expanded={isMobileMenuOpen}
                aria-label="Toggle menu"
              >
                {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
              <div className="flex items-center space-x-2 text-sm">
                <span className="text-text-subtle font-medium hidden sm:inline">Workspace</span>
                <span className="text-text-subtle/50 hidden sm:inline">/</span>
                <h1 className="font-semibold text-text-title capitalize">{path.split('/').pop() || 'Overview'}</h1>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
               <ThemeToggle />
            </div>
         </header>
         
         <div className="flex-1 p-6 md:p-8 min-h-0 overflow-y-auto bg-background">
            <Outlet />
         </div>
      </main>
    </div>
  );
}
