import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { IncomeStatementComparisonResponse } from "@/lib/api-types";

export function useIncomeStatement(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "income-statement"],
    queryFn: async () => {
      const { data } = await api.get<IncomeStatementComparisonResponse>(
        `/companies/${companyId}/income-statement`,
      );
      return data;
    },
  });
}
