import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Loader2, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";
import { withWakeupRetry } from "@/lib/retry";

export function GoogleCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("Waking up authentication server...");

  useEffect(() => {
    const oauthError = searchParams.get("error");
    if (oauthError) {
      const description = searchParams.get("error_description");
      setError(description || `Google sign-in was denied (${oauthError}).`);
      return;
    }

    const code = searchParams.get("code");
    if (!code) {
      setError("Authorization code is missing from redirect URL.");
      return;
    }

    const exchangeCode = async () => {
      try {
        setStatus("Securing token credentials...");
        await withWakeupRetry(() => api.loginWithGoogle(code));
        setStatus("Session authorized. Redirecting to workspace...");
        setTimeout(() => {
          navigate("/app/dashboard");
        }, 800);
      } catch (err: unknown) {
        console.error("Auth callback failed:", err);
        setError(
          err instanceof Error
            ? err.message
            : "Failed to authenticate your session via Google OAuth."
        );
      }
    };

    exchangeCode();
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen bg-bg-deep text-text-body flex items-center justify-center p-6 text-center animate-fade-in">
      <div className="p-8 border border-border-subtle bg-bg-surface max-w-sm w-full space-y-6">
        {error ? (
          <div className="space-y-4">
            <div className="flex items-center justify-center">
              <AlertCircle className="h-10 w-10 text-red-500" />
            </div>
            <div>
              <h3 className="font-serif italic text-2xl text-text-title mb-2">Authentication Error</h3>
              <p className="text-xs text-text-subtle uppercase tracking-widest leading-relaxed">
                {error}
              </p>
            </div>
            <button
              onClick={() => navigate("/auth/sign-in")}
              className="w-full bg-bg-deep border border-border-subtle text-text-body px-4 py-2 text-xs uppercase tracking-widest hover:border-border-accent transition-colors"
            >
              Back to Sign In
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-center">
              <Loader2 className="h-8 w-8 text-text-title animate-spin" />
            </div>
            <div>
              <h3 className="font-serif italic text-2xl text-text-title mb-2">Signing In</h3>
              <p className="text-xs text-text-subtle uppercase tracking-widest leading-relaxed">
                {status}
              </p>
            </div>
            <div className="text-[10px] uppercase tracking-widest font-mono text-text-subtle border border-border-subtle py-2">
              TLS 1.3 • AES-256 ENCRYPTED
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
