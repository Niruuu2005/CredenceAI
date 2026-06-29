import { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { api } from "@/lib/api";

export function ProtectedRoute() {
  const [status, setStatus] = useState<"loading" | "authenticated" | "unauthenticated">("loading");

  useEffect(() => {
    if (!api.isAuthenticated()) {
      setStatus("unauthenticated");
      return;
    }
    api.getCurrentUser()
      .then(() => setStatus("authenticated"))
      .catch(() => {
        api.logout();
        setStatus("unauthenticated");
      });
  }, []);

  if (status === "loading") {
    return null;
  }
  if (status === "unauthenticated") {
    return <Navigate to="/auth/sign-in" replace />;
  }
  return <Outlet />;
}
