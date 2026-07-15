import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { InsightsResponse, RecommendationsResponse, SignalsResponse } from "@/lib/api-types";

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

/** Query (GET): sinais são computados pela aplicação, sem IA — barato e sem
 * efeito colateral, pode recarregar à vontade. */
export function useAdvisorSignals(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "advisor", "signals"],
    queryFn: async () => {
      const { data } = await api.get<SignalsResponse>(`/companies/${companyId}/advisor/signals`);
      return data;
    },
  });
}

/** Mutação (POST): a narração das recomendações consome tokens de IA. */
export function useGenerateRecommendations(companyId: string) {
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<RecommendationsResponse>(
        `/companies/${companyId}/advisor/recommendations`,
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
