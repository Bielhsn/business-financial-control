import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { CatalogItemKind, CatalogItemResponse } from "@/lib/api-types";

export function useCatalogItems(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "catalog"],
    queryFn: async () => {
      const { data } = await api.get<CatalogItemResponse[]>(
        `/companies/${companyId}/catalog-items`,
      );
      return data;
    },
  });
}

export interface CatalogItemInput {
  name: string;
  description?: string | null;
  price_cents: number;
  kind: CatalogItemKind;
  tracks_inventory: boolean;
  stock_quantity?: number | null;
}

export function useCreateCatalogItem(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: CatalogItemInput) => {
      const { data } = await api.post<CatalogItemResponse>(
        `/companies/${companyId}/catalog-items`,
        input,
      );
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "catalog"] });
    },
  });
}

export function useAdjustStock(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: { itemId: string; delta: number; reason: string }) => {
      const { data } = await api.post<CatalogItemResponse>(
        `/companies/${companyId}/catalog-items/${input.itemId}/adjust-stock`,
        { delta: input.delta, reason: input.reason },
      );
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "catalog"] });
    },
  });
}
