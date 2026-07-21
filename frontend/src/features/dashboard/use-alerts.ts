import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { AlertResponse } from "@/lib/api-types";

export function useAlerts(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "alerts"],
    queryFn: async () => {
      const { data } = await api.get<AlertResponse[]>(`/companies/${companyId}/alerts`);
      return data;
    },
  });
}
