import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";

import { api } from "@/lib/api";
import type { CompanyBlueprintResponse } from "@/lib/api-types";

export function useBlueprint(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "blueprint"],
    queryFn: async () => {
      try {
        const { data } = await api.get<CompanyBlueprintResponse>(
          `/companies/${companyId}/blueprint`,
        );
        return data;
      } catch (error) {
        // 404 = empresa ainda sem blueprint gerado: estado válido, não erro.
        if (axios.isAxiosError(error) && error.response?.status === 404) {
          return null;
        }
        throw error;
      }
    },
  });
}

export function useGenerateBlueprint(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: { additional_context?: string | null }) => {
      const { data } = await api.post<CompanyBlueprintResponse>(
        `/companies/${companyId}/blueprint`,
        input,
      );
      return data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["companies", companyId, "blueprint"], data);
    },
  });
}

export function useSeedCategoriesFromBlueprint(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post(
        `/companies/${companyId}/financial-categories/seed-from-blueprint`,
      );
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "categories"] });
    },
  });
}
