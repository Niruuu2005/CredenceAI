import { useState, useEffect } from "react";
import { Outlet, Link, useLocation } from "react-router-dom";
import { LayoutDashboard, Search, Database, Bell, Settings, CreditCard } from "lucide-react";
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

  return (
    <div className="flex h-screen overflow-hidden bg-bg-deep text-text-body">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border-subtle bg-bg-deep flex flex-col flex-shrink-0 h-full overflow-hidden">
        <div className="h-16 flex items-center px-6 border-b border-border-subtle">
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-5 h-5 border border-text-subtle flex items-center justify-center rotate-45">
              <span className="-rotate-45 text-[8px] font-bold tracking-widest text-text-title">C</span>
            </div>
            <span className="font-sans font-bold tracking-widest uppercase text-xs text-logo-text-color ml-2">Credence</span>
          </Link>
        </div>
        
        <div className="p-4 flex flex-col flex-1 gap-1">
          <div className="text-[10px] uppercase tracking-[0.2em] font-medium text-text-subtle mb-2 px-2 mt-4">Workspace</div>
          {navItems.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                "flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                path === item.href ? "bg-accent text-accent-foreground" : "text-text-subtle hover:bg-bg-panel hover:text-text-title"
              )}
            >
              <item.icon className="h-4 w-4" />
              <span>{item.name}</span>
            </Link>
          ))}
          
          <div className="mt-8 text-[10px] uppercase tracking-[0.2em] font-medium text-text-subtle mb-2 px-2">Quota</div>
          <div className="px-3 py-2 space-y-2">
             <div className="flex justify-between text-xs mb-1">
                <span className="text-text-subtle">Searches ({user?.plan || "Free"})</span>
                <span className="font-mono text-text-body">{searchUsed}/{quotaLimit}</span>
             </div>
             <div className="h-1 w-full bg-border-subtle overflow-hidden">
                <div 
                   className="h-full bg-border-accent transition-all duration-500" 
                   style={{ width: `${Math.min(100, (searchUsed / quotaLimit) * 100)}%` }}
                />
             </div>
             <Link to="/app/billing" className="text-[10px] uppercase tracking-widest text-text-title hover:text-text-subtle mt-2 block font-medium">Upgrade Plan</Link>
          </div>
        </div>

        <div className="p-4 border-t border-border-subtle gap-1 flex flex-col">
          {bottomItems.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                "flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                path === item.href ? "bg-accent text-accent-foreground" : "text-text-subtle hover:bg-bg-panel hover:text-text-title"
              )}
            >
              <item.icon className="h-4 w-4" />
              <span>{item.name}</span>
            </Link>
          ))}
          <div className="mt-4 px-3 flex items-center justify-between">
             <div className="flex items-center space-x-3">
                {user?.picture ? (
                   <img src={user.picture} className="h-8 w-8 rounded-full border border-border-subtle" alt="Avatar" referrerPolicy="no-referrer" />
                ) : (
                   <div className="h-8 w-8 border border-border-subtle bg-bg-panel flex items-center justify-center text-text-title font-serif italic text-xs font-medium">
                      {user?.name ? user.name.split(' ').map((n: string) => n[0]).join('').toUpperCase() : (user?.email?.[0]?.toUpperCase() || '?')}
                   </div>
                )}
                <div className="flex flex-col min-w-0">
                   <span className="text-xs font-semibold text-text-title truncate max-w-[120px]" title={user?.name || user?.email || ""}>
                     {user?.name || user?.email || "Account"}
                   </span>
                   <span className="text-[8px] uppercase tracking-widest text-text-subtle font-medium">{user?.plan || "Free"} Tier</span>
                </div>
             </div>
             <button 
                onClick={() => {
                   api.logout();
                   window.location.href = "/auth/sign-in";
                }}
                className="text-[9px] uppercase tracking-widest text-red-500 hover:text-red-400 font-bold border border-border-subtle hover:border-red-950 px-2 py-1 bg-bg-surface hover:bg-bg-panel transition-colors cursor-pointer"
                title="Sign Out"
             >
                Exit
             </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 h-full overflow-hidden bg-bg-deep">
         <header className="h-16 border-b border-border-subtle bg-bg-deep flex items-center px-8 flex-shrink-0 justify-between">
            <h1 className="text-lg font-serif italic text-text-title capitalize">{path.split('/').pop() || 'Workspace'}</h1>
            <div className="flex items-center space-x-4">
               <ThemeToggle />
            </div>
         </header>
         <div className="flex-1 p-8 min-h-0 overflow-hidden bg-bg-deep">
            <Outlet />
         </div>
      </main>
    </div>
  );
}
