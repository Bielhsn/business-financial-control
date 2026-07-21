import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { SalesAnalyticsResponse } from "@/lib/api-types";

export function useSalesAnalytics(companyId: string, days = 30) {
  return useQuery({
    queryKey: ["companies", companyId, "analytics", "sales", days],
    queryFn: async () => {
      const { data } = await api.get<SalesAnalyticsResponse>(
        `/companies/${companyId}/analytics/sales`,
        { params: { days } },
      );
      return data;
    },
  });
}
