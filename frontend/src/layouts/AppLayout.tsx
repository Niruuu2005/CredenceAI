import { useState, useEffect } from "react";
import { Outlet, Link, useLocation } from "react-router-dom";
import { LayoutDashboard, Search, Database, Bell, Settings, CreditCard, Menu, X, LogOut } from "lucide-react";
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
    <div className="flex flex-col h-full bg-bg-deep select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-border-subtle/10 shrink-0">
        <Link to="/" className="flex items-center space-x-2">
          <div className="w-6 h-6 border-2 border-primary rounded-lg flex items-center justify-center rotate-45 bg-bg-panel neu-outset-sm">
            <span className="-rotate-45 text-[10px] font-extrabold tracking-widest text-text-title">C</span>
          </div>
          <span className="font-sans font-bold tracking-widest uppercase text-xs text-primary ml-2">Credence</span>
        </Link>
      </div>
      
      {/* Nav Links */}
      <div className="p-4 flex flex-col flex-1 gap-1.5 overflow-y-auto">
        <div className="text-[10px] uppercase tracking-[0.2em] font-semibold text-text-subtle mb-2 px-2 mt-2">Workspace</div>
        {navItems.map((item) => {
          const isActive = path === item.href;
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                "flex items-center space-x-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all",
                isActive 
                  ? "neu-inset text-primary bg-bg-panel font-semibold shadow-inner" 
                  : "text-text-subtle hover:bg-bg-panel/40 hover:text-text-title"
              )}
            >
              <item.icon className="h-4 w-4" />
              <span>{item.name}</span>
            </Link>
          );
        })}
        
        {/* Quota Section */}
        <div className="mt-6 text-[10px] uppercase tracking-[0.2em] font-semibold text-text-subtle mb-2 px-2">Quota</div>
        <div className="px-3 py-3 rounded-2xl bg-bg-panel/20 neu-inset-sm space-y-2.5 mx-1">
           <div className="flex justify-between text-xs">
              <span className="text-text-subtle">Searches ({user?.plan || "Free"})</span>
              <span className="font-mono text-text-body font-bold">{searchUsed}/{quotaLimit}</span>
           </div>
           <div className="h-2 w-full bg-bg-deep rounded-full overflow-hidden neu-inset-sm">
              <div 
                 className="h-full bg-primary rounded-full transition-all duration-500 shadow-sm" 
                 style={{ width: `${Math.min(100, (searchUsed / quotaLimit) * 100)}%` }}
              />
           </div>
           <Link to="/app/billing" className="text-[10px] uppercase tracking-wider text-primary hover:opacity-80 mt-1 block font-bold text-center">Upgrade Plan</Link>
        </div>
      </div>

      {/* User Info & Settings */}
      <div className="p-4 border-t border-border-subtle/10 gap-1 flex flex-col shrink-0">
        {bottomItems.map((item) => {
          const isActive = path === item.href;
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                "flex items-center space-x-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all",
                isActive 
                  ? "neu-inset text-primary bg-bg-panel font-semibold shadow-inner" 
                  : "text-text-subtle hover:bg-bg-panel/40 hover:text-text-title"
              )}
            >
              <item.icon className="h-4 w-4" />
              <span>{item.name}</span>
            </Link>
          );
        })}
        
        {/* Profile Card */}
        <div className="mt-4 p-3 rounded-2xl bg-bg-panel/20 neu-inset-sm flex items-center justify-between mx-1">
          <div className="flex items-center space-x-2.5 min-w-0">
             {user?.picture ? (
                <img src={user.picture} className="h-8 w-8 rounded-xl border border-border-subtle/20 bg-bg-panel" alt="Avatar" referrerPolicy="no-referrer" />
             ) : (
                <div className="h-8 w-8 rounded-xl border border-border-subtle/20 bg-bg-panel flex items-center justify-center text-text-title font-sans font-bold text-xs">
                   {user?.name ? user.name.split(' ').map((n: string) => n[0]).join('').toUpperCase() : (user?.email?.[0]?.toUpperCase() || '?')}
                </div>
             )}
             <div className="flex flex-col min-w-0">
                <span className="text-xs font-bold text-text-title truncate max-w-[100px]" title={user?.name || user?.email || ""}>
                  {user?.name || user?.email || "Account"}
                </span>
                <span className="text-[8px] uppercase tracking-widest text-text-subtle font-bold">{user?.plan || "Free"} Tier</span>
             </div>
          </div>
          <button 
             onClick={() => {
                api.logout();
                window.location.href = "/auth/sign-in";
             }}
             className="h-8 w-8 rounded-xl flex items-center justify-center text-red-500 hover:text-red-400 bg-bg-deep border-none hover:bg-bg-panel active:scale-95 cursor-pointer neu-outset-sm transition-all"
             title="Sign Out"
          >
             <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen overflow-hidden bg-bg-deep text-text-body font-sans">
      {/* Desktop Sidebar (visible on screens >= 1024px) */}
      <aside className="hidden lg:flex w-64 bg-bg-deep flex-col flex-shrink-0 h-full overflow-hidden border-r border-border-subtle/10 neu-outset-sm z-30">
        <SidebarContent />
      </aside>

      {/* Mobile Drawer (visible on screens < 1024px) */}
      <div 
        className={cn(
          "fixed inset-0 z-50 bg-black/40 backdrop-blur-xs transition-opacity duration-300 lg:hidden",
          isMobileMenuOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        )}
        onClick={() => setIsMobileMenuOpen(false)}
      />
      <aside 
        className={cn(
          "fixed top-0 bottom-0 left-0 z-50 w-64 bg-bg-deep flex flex-col h-full shadow-2xl transition-transform duration-300 ease-in-out lg:hidden",
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <SidebarContent />
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 h-full overflow-hidden bg-bg-deep relative">
         <header className="h-16 bg-bg-deep flex items-center px-6 shrink-0 justify-between z-20 neu-outset-sm border-b border-border-subtle/5">
            <div className="flex items-center space-x-3">
              {/* Hamburger Button for mobile */}
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="lg:hidden p-2 rounded-xl text-text-body hover:bg-bg-panel/40 active:scale-95 neu-outset-sm transition-all cursor-pointer"
                aria-expanded={isMobileMenuOpen}
                aria-label="Toggle menu"
              >
                {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
              <h1 className="text-lg font-serif italic text-text-title capitalize font-medium">{path.split('/').pop() || 'Workspace'}</h1>
            </div>
            
            <div className="flex items-center space-x-4">
               <ThemeToggle />
            </div>
         </header>
         
         <div className="flex-1 p-6 md:p-8 min-h-0 overflow-y-auto bg-bg-deep">
            <Outlet />
         </div>
      </main>
    </div>
  );
}
