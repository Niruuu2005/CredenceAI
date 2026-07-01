import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import React, { useState } from "react";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { withWakeupRetry } from "@/lib/retry";

const isLocalDev =
  import.meta.env.DEV || import.meta.env.VITE_APP_ENV === "local";

export function SignUp() {
  const navigate = useNavigate();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [authProvider, setAuthProvider] = useState<"Google" | "GitHub" | null>(null);

  const startOAuthSignUp = async (provider: "Google" | "GitHub") => {
    setIsAuthenticating(true);
    setAuthProvider(provider);
    setErrorMessage(null);

    try {
      const { url, mock } =
        provider === "Google"
          ? await withWakeupRetry(() => api.getGoogleAuthUrl())
          : await withWakeupRetry(() => api.getGitHubAuthUrl());

      if (mock) {
        if (!isLocalDev) {
          setErrorMessage(`${provider} OAuth is not configured for this environment.`);
          setIsAuthenticating(false);
          return;
        }
        if (provider === "Google") {
          await api.loginWithGoogle("mock_dev_code");
        } else {
          await api.loginWithGitHub("mock_github_code");
        }
        navigate("/app/dashboard");
        return;
      }
      window.location.href = url;
    } catch (err) {
      console.error(`Failed to start ${provider} sign-up:`, err);
      setErrorMessage(`Failed to start ${provider} sign-up.`);
      setIsAuthenticating(false);
    }
  };

  const handleOAuth = async (provider: "Google" | "GitHub") => {
    await startOAuthSignUp(provider);
  };

  return (
    <div className="space-y-6 bg-bg-deep text-text-body">
      {isAuthenticating && (
         <div className="fixed inset-0 z-50 bg-bg-deep/90 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center animate-fade-in text-text-body">
           <div className="p-8 border border-border-subtle bg-bg-surface max-w-sm w-full space-y-6">
             <div className="flex items-center justify-center">
               <Loader2 className="h-8 w-8 text-text-title animate-spin" />
             </div>
             <div>
               <h3 className="font-serif italic text-2xl text-text-title mb-2">Connecting to Account</h3>
               <p className="text-xs text-text-subtle uppercase tracking-widest leading-relaxed">
                 Authenticating your credentials securely via {authProvider}...
               </p>
             </div>
             <div className="text-[10px] uppercase tracking-widest font-mono text-text-subtle border border-border-subtle py-2">
               TLS 1.3 • AES-256 ENCRYPTED
             </div>
           </div>
         </div>
      )}

      <div>
        <h1 className="text-3xl font-serif italic tracking-tight text-text-title">Create an account</h1>
        <p className="text-[10px] uppercase tracking-widest text-text-subtle mt-2 font-medium">
          Sign up with Google or GitHub. Accounts are created on first login.
        </p>
      </div>

      {errorMessage && (
        <div className="p-3 border border-red-500 bg-red-500/10 text-red-500 text-xs font-mono rounded">
          {errorMessage}
        </div>
      )}

      <Button type="button" className="w-full" onClick={() => handleOAuth("Google")}>
        Continue with Google
      </Button>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t border-border-subtle" />
        </div>
        <div className="relative flex justify-center text-[10px] uppercase tracking-widest font-bold">
          <span className="bg-bg-deep px-4 text-text-subtle border border-border-subtle">Or</span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        <Button
          variant="outline"
          onClick={() => handleOAuth("GitHub")}
          className="border-border-subtle bg-bg-surface text-[10px] uppercase tracking-[0.2em] font-medium h-12 text-text-body hover:bg-bg-panel hover:text-text-title"
        >
          Continue with GitHub
        </Button>
      </div>

      <p className="px-8 text-center text-[10px] uppercase tracking-widest text-text-subtle font-medium">
        Already have an account?{" "}
        <Link to="/auth/sign-in" className="text-text-body hover:text-text-title transition-colors underline underline-offset-4">
          Sign in
        </Link>
      </p>

      <p className="px-8 text-center text-[10px] uppercase tracking-[0.2em] leading-loose text-text-subtle font-medium">
        By continuing, you agree to our{" "}
        <Link to="/terms" className="text-text-body hover:text-text-title transition-colors underline underline-offset-4">
          Terms of Service
        </Link>{" "}
        and{" "}
        <Link to="/privacy" className="text-text-body hover:text-text-title transition-colors underline underline-offset-4">
          Privacy Policy
        </Link>
        .
      </p>
    </div>
  );
}
