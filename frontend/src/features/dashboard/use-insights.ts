import { useMutation } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { InsightsResponse } from "@/lib/api-types";

interface PeriodInput {
  start: string;
  end: string;
}

/** Mutação (POST), não query: gerar insights consome tokens de IA — nunca deve
 * disparar por refetch automático. */
export function useGenerateInsights(companyId: string) {
  return useMutation({
    mutationFn: async (input: PeriodInput) => {
      const { data } = await api.post<InsightsResponse>(`/companies/${companyId}/insights`, input);
      return data;
    },
  });
}

export function useGeneratePeriodSummary(companyId: string) {
  return useMutation({
    mutationFn: async (input: PeriodInput) => {
      const { data } = await api.post<{ summary: string }>(
        `/companies/${companyId}/insights/summary`,
        input,
      );
      return data;
    },
  });
}

export function useAskQuestion(companyId: string) {
  return useMutation({
    mutationFn: async (input: PeriodInput & { question: string }) => {
      const { data } = await api.post<{ answer: string }>(
        `/companies/${companyId}/insights/ask`,
        input,
      );
      return data;
    },
  });
}
