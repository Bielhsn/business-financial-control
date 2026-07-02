import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { DashboardSummaryResponse } from "@/lib/api-types";

export interface DashboardParams {
  start: string;
  end: string;
  months?: number;
}

export function useDashboard(companyId: string, params: DashboardParams) {
  return useQuery({
    queryKey: ["companies", companyId, "dashboard", params],
    queryFn: async () => {
      const { data } = await api.get<DashboardSummaryResponse>(
        `/companies/${companyId}/dashboard`,
        { params },
      );
      return data;
    },
  });
}
