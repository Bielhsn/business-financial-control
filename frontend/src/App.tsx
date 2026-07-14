import { Suspense, lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { CompanyLayout } from "@/app/company-layout";
import { ProtectedRoute } from "@/app/protected-route";

// Rotas carregadas sob demanda (code splitting): o bundle inicial fica leve
// mesmo com páginas pesadas (gráficos etc.).
const LandingPage = lazy(() =>
  import("@/features/landing/landing-page").then((m) => ({ default: m.LandingPage })),
);
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
  import("@/features/dashboard/dashboard-page").then((m) => ({ default: m.DashboardPage })),
);
const TransactionsPage = lazy(() =>
  import("@/features/financial/transactions-page").then((m) => ({
    default: m.TransactionsPage,
  })),
);
const ClientsPage = lazy(() =>
  import("@/features/clients/clients-page").then((m) => ({ default: m.ClientsPage })),
);
const CatalogPage = lazy(() =>
  import("@/features/catalog/catalog-page").then((m) => ({ default: m.CatalogPage })),
);
const EmployeesPage = lazy(() =>
  import("@/features/employees/employees-page").then((m) => ({ default: m.EmployeesPage })),
);
const AgendaPage = lazy(() =>
  import("@/features/modules/coming-soon-page").then((m) => ({ default: m.AgendaPage })),
);
const SubscriptionsPage = lazy(() =>
  import("@/features/modules/coming-soon-page").then((m) => ({ default: m.SubscriptionsPage })),
);
const ProjectsPage = lazy(() =>
  import("@/features/modules/coming-soon-page").then((m) => ({ default: m.ProjectsPage })),
);
const ContractsPage = lazy(() =>
  import("@/features/modules/coming-soon-page").then((m) => ({ default: m.ContractsPage })),
);
const CompanySettingsPage = lazy(() =>
  import("@/features/settings/company-settings-page").then((m) => ({
    default: m.CompanySettingsPage,
  })),
);
const IntegrationsPage = lazy(() =>
  import("@/features/integrations/integrations-page").then((m) => ({
    default: m.IntegrationsPage,
  })),
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
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/companies" element={<CompaniesPage />} />
          <Route path="/onboarding" element={<OnboardingPage />} />
          <Route path="/c/:companyId" element={<CompanyLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="transactions" element={<TransactionsPage />} />
            <Route path="clients" element={<ClientsPage />} />
            <Route path="catalog" element={<CatalogPage />} />
            <Route path="employees" element={<EmployeesPage />} />
            <Route path="agenda" element={<AgendaPage />} />
            <Route path="subscriptions" element={<SubscriptionsPage />} />
            <Route path="projects" element={<ProjectsPage />} />
            <Route path="contracts" element={<ContractsPage />} />
            <Route path="settings" element={<CompanySettingsPage />} />
            <Route path="integrations" element={<IntegrationsPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/companies" replace />} />
      </Routes>
    </Suspense>
  );
}
