import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import React, { useState } from "react";
import { Loader2, ShieldAlert } from "lucide-react";
import { api } from "@/lib/api";
import { withWakeupRetry } from "@/lib/retry";

const isLocalDev =
  import.meta.env.DEV || import.meta.env.VITE_APP_ENV === "local";

export function SignIn() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [authProvider, setAuthProvider] = useState<"Google" | "GitHub" | "Email" | null>(null);

  const completeGoogleAuth = async (mock: boolean, url: string) => {
    if (mock) {
      if (!isLocalDev) {
        setErrorMessage("Google OAuth is not configured for this environment.");
        setIsAuthenticating(false);
        return;
      }
      await api.loginWithGoogle("mock_dev_code");
      navigate("/app/dashboard");
      return;
    }
    window.location.href = url;
  };

  const completeGitHubAuth = async (mock: boolean, url: string) => {
    if (mock) {
      if (!isLocalDev) {
        setErrorMessage("GitHub OAuth is not configured for this environment.");
        setIsAuthenticating(false);
        return;
      }
      await api.loginWithGitHub("mock_github_code");
      navigate("/app/dashboard");
      return;
    }
    window.location.href = url;
  };

  const handleOAuth = async (provider: "Google" | "GitHub") => {
    setIsAuthenticating(true);
    setAuthProvider(provider);
    setErrorMessage(null);

    if (provider === "Google") {
      try {
        const { url, mock } = await withWakeupRetry(() => api.getGoogleAuthUrl());
        await completeGoogleAuth(mock, url);
      } catch (err) {
        console.error("Failed to resolve Google auth URL:", err);
        setErrorMessage("Failed to check Google OAuth settings.");
        setIsAuthenticating(false);
      }
    } else {
      try {
        const { url, mock } = await withWakeupRetry(() => api.getGitHubAuthUrl());
        await completeGitHubAuth(mock, url);
      } catch (err) {
        console.error("Failed to resolve GitHub auth URL:", err);
        setErrorMessage("Failed to check GitHub OAuth settings.");
        setIsAuthenticating(false);
      }
    }
  };

  const handleEmailSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setIsAuthenticating(true);
    setAuthProvider("Email");
    setErrorMessage(null);

    try {
      if (password) {
        if (!isLocalDev) {
          setErrorMessage("Developer credentials login is only available in local development.");
          setIsAuthenticating(false);
          return;
        }
        await api.loginWithCredentials(email, password);
        navigate("/app/dashboard");
        return;
      }

      const { url, mock } = await api.getGoogleAuthUrl();
      await completeGoogleAuth(mock, url);
    } catch (err: unknown) {
      console.error("Failed email/credentials sign-in:", err);
      setErrorMessage(err instanceof Error ? err.message : "Failed to authenticate session.");
    } finally {
      setIsAuthenticating(false);
    }
  };

  return (
    <div className="p-6 md:p-8 rounded-2xl bg-background-surface border border-border-subtle shadow-card text-text-body space-y-6">
      {isAuthenticating && (
         <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center animate-fade-in text-text-body">
            <div className="p-8 rounded-2xl bg-background-surface border border-border-subtle shadow-2xl max-w-sm w-full space-y-6">
              <div className="flex items-center justify-center">
                <Loader2 className="h-8 w-8 text-primary animate-spin" />
              </div>
              <div>
                <h3 className="text-xl font-bold tracking-tight text-text-title mb-2">Connecting to Account</h3>
                <p className="text-xs text-text-subtle leading-relaxed font-medium">
                  Authenticating your credentials securely via {authProvider}...
                </p>
              </div>
              <div className="text-[10px] uppercase tracking-wider font-mono text-text-subtle rounded-xl bg-background-deep border border-border-subtle py-2 mx-auto w-fit px-4">
                TLS 1.3 • AES-256 ENCRYPTED
              </div>
            </div>
         </div>
      )}

      <div>
        <h1 className="text-3xl font-bold tracking-tight text-text-title">Welcome back</h1>
        <p className="text-xs text-text-subtle mt-1.5 font-medium">
          Enter your email/username to sign in to your workspace.
        </p>
      </div>

      <form onSubmit={handleEmailSignIn} className="space-y-4">
        {errorMessage && (
          <div className="p-3 bg-red-500/10 border-l-4 border-red-500 text-red-500 text-xs font-mono rounded-xl flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}
        <div className="space-y-2">
          <label className="text-[10px] uppercase tracking-widest font-extrabold leading-none text-text-subtle ml-1" htmlFor="email">
            Email or Username
          </label>
          <Input
            id="email"
            placeholder="m@example.com or username"
            type="text"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoCapitalize="none"
            autoComplete="email"
            autoCorrect="off"
            required
          />
        </div>
        {isLocalDev && (
          <div className="space-y-2">
            <label className="text-[10px] uppercase tracking-widest font-extrabold leading-none text-text-subtle ml-1" htmlFor="password">
              Password (developer login)
            </label>
            <Input
              id="password"
              placeholder="••••••••"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoCapitalize="none"
              autoComplete="current-password"
            />
          </div>
        )}
        <Button type="submit" className="w-full mt-2">Sign In</Button>
      </form>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t border-border-subtle" />
        </div>
        <div className="relative flex justify-center text-[10px] uppercase tracking-widest font-bold">
          <span className="bg-background-surface border border-border-subtle px-4 text-text-subtle rounded-full py-0.5 shadow-xs">Or continue with</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Button 
          variant="outline" 
          onClick={() => handleOAuth("GitHub")}
          className="h-11"
        >
          GitHub
        </Button>
        <Button 
          variant="outline" 
          onClick={() => handleOAuth("Google")}
          className="flex items-center gap-2 justify-center h-11"
        >
          <img src="https://www.gstatic.com/images/branding/product/1x/gsa_512dp.png" className="h-4 w-4 shrink-0" alt="Google" referrerPolicy="no-referrer" />
          Google
        </Button>
      </div>

      <p className="px-8 text-center text-[10px] uppercase tracking-widest text-text-subtle font-bold">
        Don&apos;t have an account?{" "}
        <Link to="/auth/sign-up" className="text-primary hover:opacity-80 transition-colors underline underline-offset-4 font-extrabold">
          Sign up
        </Link>
      </p>
    </div>
  );
}
