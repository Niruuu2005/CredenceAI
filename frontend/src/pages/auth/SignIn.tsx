import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import React, { useState } from "react";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";

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
        const { url, mock } = await api.getGoogleAuthUrl();
        await completeGoogleAuth(mock, url);
      } catch (err) {
        console.error("Failed to resolve Google auth URL:", err);
        setErrorMessage("Failed to check Google OAuth settings.");
        setIsAuthenticating(false);
      }
    } else {
      try {
        const { url, mock } = await api.getGitHubAuthUrl();
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
        <h1 className="text-3xl font-serif italic tracking-tight text-text-title">Welcome back</h1>
        <p className="text-[10px] uppercase tracking-widest text-text-subtle mt-2 font-medium">
          Enter your email/username to sign in to your workspace.
        </p>
      </div>
      <form onSubmit={handleEmailSignIn} className="space-y-4">
        {errorMessage && (
          <div className="p-3 border border-red-500 bg-red-500/10 text-red-500 text-xs font-mono rounded">
            {errorMessage}
          </div>
        )}
        <div className="space-y-2">
          <label className="text-[10px] uppercase tracking-widest font-bold leading-none text-text-subtle" htmlFor="email">
            Email or Username
          </label>
          <input
            id="email"
            className="flex h-12 w-full border border-border-subtle bg-bg-surface px-4 py-2 text-sm transition-colors placeholder:text-text-subtle focus-visible:outline-none focus-visible:border-border-accent text-text-body"
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
            <label className="text-[10px] uppercase tracking-widest font-bold leading-none text-text-subtle" htmlFor="password">
              Password (developer login)
            </label>
            <input
              id="password"
              className="flex h-12 w-full border border-border-subtle bg-bg-surface px-4 py-2 text-sm transition-colors placeholder:text-text-subtle focus-visible:outline-none focus-visible:border-border-accent text-text-body"
              placeholder="••••••••"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoCapitalize="none"
              autoComplete="current-password"
            />
          </div>
        )}
        <Button type="submit" className="w-full">Sign In</Button>
      </form>
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t border-border-subtle" />
        </div>
        <div className="relative flex justify-center text-[10px] uppercase tracking-widest font-bold">
          <span className="bg-bg-deep px-4 text-text-subtle border border-border-subtle">Or continue with</span>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Button 
          variant="outline" 
          onClick={() => handleOAuth("GitHub")}
          className="border-border-subtle bg-bg-surface text-[10px] uppercase tracking-[0.2em] font-medium h-12 text-text-body hover:bg-bg-panel hover:text-text-title"
        >
          GitHub
        </Button>
        <Button 
          variant="outline" 
          onClick={() => handleOAuth("Google")}
          className="border-border-subtle bg-bg-surface text-[10px] uppercase tracking-[0.2em] font-medium h-12 text-text-body hover:border-border-accent flex items-center gap-2 justify-center"
        >
          <img src="https://www.gstatic.com/images/branding/product/1x/gsa_512dp.png" className="h-4 w-4 shrink-0" alt="Google" referrerPolicy="no-referrer" />
          Google
        </Button>
      </div>
      <p className="px-8 text-center text-[10px] uppercase tracking-widest text-text-subtle font-medium">
        Don&apos;t have an account?{" "}
        <Link to="/auth/sign-up" className="text-text-body hover:text-text-title transition-colors underline underline-offset-4">
          Sign up
        </Link>
      </p>
    </div>
  );
}
