import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useSessionBootstrap } from "@/features/auth/use-auth";
import { useAuthStore } from "@/stores/auth";

export function ProtectedRoute() {
  const isBootstrapping = useSessionBootstrap();
  const accessToken = useAuthStore((s) => s.accessToken);
  const location = useLocation();

  if (isBootstrapping) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div
          role="status"
          aria-label="Carregando"
          className="size-8 animate-spin rounded-full border-2 border-primary border-t-transparent"
        />
      </div>
    );
  }

  if (accessToken === null) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
