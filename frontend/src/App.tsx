import { Suspense, lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { CompanyLayout } from "@/app/company-layout";
import { ProtectedRoute } from "@/app/protected-route";

// Rotas carregadas sob demanda (code splitting): o bundle inicial fica leve
// mesmo quando páginas pesadas (gráficos etc.) forem adicionadas.
const LoginPage = lazy(() =>
  import("@/features/auth/login-page").then((m) => ({ default: m.LoginPage })),
);
const RegisterPage = lazy(() =>
  import("@/features/auth/register-page").then((m) => ({ default: m.RegisterPage })),
);
const CompaniesPage = lazy(() =>
  import("@/features/companies/companies-page").then((m) => ({ default: m.CompaniesPage })),
);
const OnboardingPage = lazy(() =>
  import("@/features/onboarding/onboarding-page").then((m) => ({ default: m.OnboardingPage })),
);
const DashboardPage = lazy(() =>
  import("@/pages/dashboard-page").then((m) => ({ default: m.DashboardPage })),
);

function PageFallback() {
  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <div
        role="status"
        aria-label="Carregando"
        className="size-8 animate-spin rounded-full border-2 border-primary border-t-transparent"
      />
    </div>
  );
}

export function App() {
  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/companies" element={<CompaniesPage />} />
          <Route path="/onboarding" element={<OnboardingPage />} />
          <Route path="/c/:companyId" element={<CompanyLayout />}>
            <Route index element={<DashboardPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/companies" replace />} />
      </Routes>
    </Suspense>
  );
}
