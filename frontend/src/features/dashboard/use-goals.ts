import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { GoalMetric, GoalProgressResponse } from "@/lib/api-types";

export function useGoals(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "goals"],
    queryFn: async () => {
      const { data } = await api.get<GoalProgressResponse[]>(`/companies/${companyId}/goals`);
      return data;
    },
  });
}

export function useSetGoal(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: { metric: GoalMetric; target_cents: number }) => {
      const { data } = await api.put<GoalProgressResponse[]>(
        `/companies/${companyId}/goals/${input.metric}`,
        { target_cents: input.target_cents },
      );
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["companies", companyId, "goals"] }),
  });
}

export function useDeleteGoal(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (metric: GoalMetric) => {
      await api.delete(`/companies/${companyId}/goals/${metric}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["companies", companyId, "goals"] }),
  });
}
