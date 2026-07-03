import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import React, { useState } from "react";
import { Loader2, ShieldAlert } from "lucide-react";
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
    <div className="p-6 md:p-8 rounded-2xl bg-bg-deep neu-outset text-text-body space-y-6">
      {isAuthenticating && (
         <div className="fixed inset-0 z-50 bg-bg-deep/80 backdrop-blur-xs flex flex-col items-center justify-center p-6 text-center animate-fade-in text-text-body">
            <div className="p-8 rounded-2xl bg-bg-deep neu-outset max-w-sm w-full space-y-6 border-none">
              <div className="flex items-center justify-center">
                <Loader2 className="h-8 w-8 text-primary animate-spin" />
              </div>
              <div>
                <h3 className="font-serif italic text-2xl text-text-title mb-2">Connecting to Account</h3>
                <p className="text-xs text-text-subtle uppercase tracking-widest leading-relaxed">
                  Authenticating your credentials securely via {authProvider}...
                </p>
              </div>
              <div className="text-[10px] uppercase tracking-widest font-mono text-text-subtle rounded-xl bg-bg-panel/40 py-2.5 mx-auto w-fit px-4 neu-inset-sm">
                TLS 1.3 • AES-256 ENCRYPTED
              </div>
            </div>
         </div>
      )}

      <div>
        <h1 className="text-3xl font-serif italic tracking-tight text-text-title">Create an account</h1>
        <p className="text-[10px] uppercase tracking-widest text-text-subtle mt-2 font-bold">
          Sign up with Google or GitHub. Accounts are created on first login.
        </p>
      </div>

      {errorMessage && (
        <div className="p-3 bg-red-500/10 border-l-4 border-red-500 text-red-500 text-xs font-mono rounded-xl flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      <Button type="button" className="w-full flex items-center gap-2 justify-center" onClick={() => handleOAuth("Google")}>
        <img src="https://www.gstatic.com/images/branding/product/1x/gsa_512dp.png" className="h-4 w-4 shrink-0" alt="Google" referrerPolicy="no-referrer" />
        Continue with Google
      </Button>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t border-border-subtle/10" />
        </div>
        <div className="relative flex justify-center text-[10px] uppercase tracking-widest font-bold">
          <span className="bg-bg-deep px-4 text-text-subtle rounded-full py-0.5 neu-inset-sm">Or</span>
        </div>
      </div>

      <div className="grid grid-cols-1">
        <Button
          variant="outline"
          onClick={() => handleOAuth("GitHub")}
          className="w-full"
        >
          Continue with GitHub
        </Button>
      </div>

      <p className="px-8 text-center text-[10px] uppercase tracking-widest text-text-subtle font-bold">
        Already have an account?{" "}
        <Link to="/auth/sign-in" className="text-primary hover:opacity-80 transition-colors underline underline-offset-4 font-extrabold">
          Sign in
        </Link>
      </p>

      <p className="px-4 text-center text-[9px] uppercase tracking-wider leading-relaxed text-text-subtle font-semibold">
        By continuing, you agree to our{" "}
        <Link to="/terms" className="text-text-body hover:text-text-title transition-colors underline underline-offset-3">
          Terms of Service
        </Link>{" "}
        and{" "}
        <Link to="/privacy" className="text-text-body hover:text-text-title transition-colors underline underline-offset-3">
          Privacy Policy
        </Link>
        .
      </p>
    </div>
  );
}
