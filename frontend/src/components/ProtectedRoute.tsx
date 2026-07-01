import { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { withWakeupRetry } from "@/lib/retry";

export function ProtectedRoute() {
  const [status, setStatus] = useState<"loading" | "authenticated" | "unauthenticated">("loading");

  useEffect(() => {
    if (!api.isAuthenticated()) {
      setStatus("unauthenticated");
      return;
    }
    withWakeupRetry(() => api.getCurrentUser())
      .then(() => setStatus("authenticated"))
      .catch(() => {
        api.logout();
        setStatus("unauthenticated");
      });
  }, []);

  if (status === "loading") {
    return (
      <div className="flex h-screen items-center justify-center bg-bg-deep text-text-body">
        <div className="flex flex-col items-center gap-3 text-center">
          <Loader2 className="h-6 w-6 animate-spin text-highlight-color" />
          <p className="text-xs uppercase tracking-widest text-text-subtle">
            Waking up workspace...
          </p>
        </div>
      </div>
    );
  }
  if (status === "unauthenticated") {
    return <Navigate to="/auth/sign-in" replace />;
  }
  return <Outlet />;
}
