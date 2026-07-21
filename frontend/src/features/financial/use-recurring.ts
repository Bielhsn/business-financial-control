import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  CreateRecurringRequest,
  RecurrenceFrequency,
  RecurringResponse,
} from "@/lib/api-types";

export const FREQUENCY_LABELS: Record<RecurrenceFrequency, string> = {
  weekly: "Semanal",
  monthly: "Mensal",
  yearly: "Anual",
};

export function useRecurring(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "recurring"],
    queryFn: async () => {
      const { data } = await api.get<RecurringResponse[]>(`/companies/${companyId}/recurring`);
      return data;
    },
  });
}

export function useCreateRecurring(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: CreateRecurringRequest) => {
      const { data } = await api.post<RecurringResponse>(
        `/companies/${companyId}/recurring`,
        input,
      );
      return data;
    },
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["companies", companyId, "recurring"] }),
  });
}

export function useDeleteRecurring(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (recurringId: string) => {
      await api.delete(`/companies/${companyId}/recurring/${recurringId}`);
    },
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["companies", companyId, "recurring"] }),
  });
}

export function useRunRecurring(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<{ created: number }>(
        `/companies/${companyId}/recurring/run`,
        {},
      );
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "recurring"] });
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "transactions"] });
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "dashboard"] });
    },
  });
}
