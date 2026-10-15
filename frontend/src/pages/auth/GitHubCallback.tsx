import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Loader2, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";
import { withWakeupRetry } from "@/lib/retry";

export function GitHubCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("Waking up authentication server...");

  useEffect(() => {
    const oauthError = searchParams.get("error");
    if (oauthError) {
      const description = searchParams.get("error_description");
      setError(description || `GitHub sign-in was denied (${oauthError}).`);
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
        await withWakeupRetry(() => api.loginWithGitHub(code));
        setStatus("Session authorized. Redirecting to workspace...");
        setTimeout(() => {
          navigate("/app/dashboard");
        }, 800);
      } catch (err: unknown) {
        console.error("GitHub auth callback failed:", err);
        setError(
          err instanceof Error
            ? err.message
            : "Failed to authenticate your session via GitHub OAuth."
        );
      }
    };

    exchangeCode();
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen bg-bg-deep text-text-body flex items-center justify-center p-6 text-center animate-fade-in">
      <div className="p-8 border border-border-subtle bg-background-surface rounded-2xl max-w-sm w-full space-y-6 shadow-2xl">
        {error ? (
          <div className="space-y-4">
            <div className="flex items-center justify-center">
              <AlertCircle className="h-10 w-10 text-red-500" />
            </div>
            <div>
              <h3 className="text-xl font-bold tracking-tight text-text-title mb-2">Authentication Error</h3>
              <p className="text-xs text-text-subtle leading-relaxed font-medium">
                {error}
              </p>
            </div>
            <button
              onClick={() => navigate("/auth/sign-in")}
              className="w-full bg-background-deep border border-border-subtle text-text-body px-4 py-2.5 text-xs font-semibold rounded-xl hover:border-border-accent transition-colors"
            >
              Back to Sign In
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-center">
              <Loader2 className="h-8 w-8 text-primary animate-spin" />
            </div>
            <div>
              <h3 className="text-xl font-bold tracking-tight text-text-title mb-2">Signing In</h3>
              <p className="text-xs text-text-subtle leading-relaxed font-medium">
                {status}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
