import { useMutation } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { InsightsResponse } from "@/lib/api-types";

/** Mutação (POST), não query: gerar insights consome tokens de IA — nunca deve
 * disparar por refetch automático. */
export function useGenerateInsights(companyId: string) {
  return useMutation({
    mutationFn: async (input: { start: string; end: string }) => {
      const { data } = await api.post<InsightsResponse>(`/companies/${companyId}/insights`, input);
      return data;
    },
  });
}
