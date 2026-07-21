import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { HealthScoreResponse } from "@/lib/api-types";

export function useHealthScore(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "analytics", "health"],
    queryFn: async () => {
      const { data } = await api.get<HealthScoreResponse>(
        `/companies/${companyId}/analytics/health`,
      );
      return data;
    },
  });
}
