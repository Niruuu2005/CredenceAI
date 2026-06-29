import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { MarketingLayout } from "./layouts/MarketingLayout";
import { AppLayout } from "./layouts/AppLayout";
import { AuthLayout } from "./layouts/AuthLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";

// Marketing
import { Home } from "./pages/marketing/Home";
import { Pricing } from "./pages/marketing/Pricing";
import { Features } from "./pages/marketing/Features";
import { Docs } from "./pages/marketing/Docs";
import { Enterprise } from "./pages/marketing/Enterprise";
import { Legal } from "./pages/marketing/Legal";

// Auth
import { SignIn } from "./pages/auth/SignIn";
import { SignUp } from "./pages/auth/SignUp";
import { GoogleCallback } from "./pages/auth/GoogleCallback";

// App
import { Dashboard } from "./pages/app/Dashboard";
import { SearchApp } from "./pages/app/SearchApp";
import { Billing } from "./pages/app/Billing";
import { Collections } from "./pages/app/Collections";
import { Monitors } from "./pages/app/Monitors";
import { Settings } from "./pages/app/Settings";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Marketing Routes */}
        <Route element={<MarketingLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/features" element={<Features />} />
          <Route path="/docs" element={<Docs />} />
          <Route path="/enterprise" element={<Enterprise />} />
          <Route path="/legal" element={<Legal />} />
          <Route path="/privacy" element={<Navigate to="/legal?tab=privacy" replace />} />
          <Route path="/terms" element={<Navigate to="/legal?tab=terms" replace />} />
          <Route path="/security" element={<Navigate to="/legal?tab=security" replace />} />
        </Route>

        {/* Auth Routes */}
        <Route path="/auth" element={<AuthLayout />}>
           <Route path="sign-in" element={<SignIn />} />
           <Route path="sign-up" element={<SignUp />} />
           <Route path="google/callback" element={<GoogleCallback />} />
        </Route>

        {/* App Routes */}
        <Route path="/app" element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="search" element={<SearchApp />} />
            <Route path="collections" element={<Collections />} />
            <Route path="monitors" element={<Monitors />} />
            <Route path="settings" element={<Settings />} />
            <Route path="billing" element={<Billing />} />
          </Route>
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

