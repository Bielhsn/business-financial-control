import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { AccountsSummaryResponse } from "@/lib/api-types";

export function useAccounts(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "accounts"],
    queryFn: async () => {
      const { data } = await api.get<AccountsSummaryResponse>(`/companies/${companyId}/accounts`);
      return data;
    },
  });
}
