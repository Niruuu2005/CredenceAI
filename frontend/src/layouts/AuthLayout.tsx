import { Outlet, Link } from "react-router-dom";
import { Activity } from "lucide-react";

export function AuthLayout() {
  return (
    <div className="min-h-screen flex bg-bg-deep text-text-body transition-colors duration-300">
      <div className="flex-1 flex flex-col justify-center px-4 sm:px-6 lg:flex-none lg:px-20 xl:px-24 bg-bg-deep w-full lg:w-[480px] shrink-0 border-r border-border-subtle relative z-10">
        <div className="mx-auto w-full max-w-sm">
          <Link to="/" className="flex items-center space-x-2 mb-12">
            <div className="w-8 h-8 border border-text-subtle flex items-center justify-center rotate-45">
              <span className="-rotate-45 text-xs font-bold tracking-widest text-text-title">C</span>
            </div>
            <span className="text-sm tracking-[0.4em] uppercase font-light text-logo-text-color ml-2">Credence</span>
          </Link>
          <Outlet />
        </div>
      </div>
      <div className="hidden lg:block relative w-0 flex-1 bg-bg-surface text-text-body">
        <div className="absolute inset-0 flex flex-col justify-center p-24">
           <div className="max-w-xl">
             <h2 className="text-5xl font-serif italic mb-8 leading-tight text-text-title">Intelligence is opaque. <br/><span className="text-text-subtle">Trust requires proof.</span></h2>
             <p className="text-sm tracking-wide text-text-body mb-12 font-sans border-l border-border-subtle pl-6 leading-relaxed">
               Join thousands of analysts and researchers who rely on CredenceAI to search, score, and verify information across billions of unstructured sources.
             </p>
             <div className="flex gap-6 items-center mt-12 p-8 border border-border-subtle bg-bg-deep">
                <div className="h-14 w-14 border border-border-subtle flex items-center justify-center shrink-0 bg-bg-surface">
                  <Activity className="h-6 w-6 text-highlight-color" />
                </div>
                <div>
                   <div className="font-serif italic text-2xl text-text-title mb-2">Enterprise Verified</div>
                   <div className="text-text-subtle text-[10px] uppercase tracking-widest font-sans">SOC2 Type II Compliant &bull; E2E Encryption</div>
                </div>
             </div>
           </div>
        </div>
      </div>
    </div>
  );
}
