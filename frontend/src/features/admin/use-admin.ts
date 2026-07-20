import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { AdminOverviewResponse } from "@/lib/api-types";

export function useIsPlatformAdmin() {
  return useQuery({
    queryKey: ["admin", "me"],
    queryFn: async () => {
      const { data } = await api.get<{ is_platform_admin: boolean }>("/admin/me");
      return data.is_platform_admin;
    },
    staleTime: 1000 * 60 * 5,
  });
}

export function useAdminOverview(enabled: boolean) {
  return useQuery({
    queryKey: ["admin", "overview"],
    queryFn: async () => {
      const { data } = await api.get<AdminOverviewResponse>("/admin/overview");
      return data;
    },
    enabled,
  });
}
