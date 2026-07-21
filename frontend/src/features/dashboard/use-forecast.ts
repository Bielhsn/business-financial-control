import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { CashflowForecastResponse } from "@/lib/api-types";

export function useCashflowForecast(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "analytics", "forecast"],
    queryFn: async () => {
      const { data } = await api.get<CashflowForecastResponse>(
        `/companies/${companyId}/analytics/forecast`,
      );
      return data;
    },
  });
}
