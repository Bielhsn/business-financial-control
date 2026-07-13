import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { ParsedImportRow } from "@/lib/csv";

export interface ImportTransactionsResult {
  imported: number;
  categories_created: number;
}

export function useImportTransactions(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (rows: ParsedImportRow[]) => {
      const { data } = await api.post<ImportTransactionsResult>(
        `/companies/${companyId}/transactions/import`,
        { rows },
      );
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "transactions"] });
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "categories"] });
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "dashboard"] });
    },
  });
}
