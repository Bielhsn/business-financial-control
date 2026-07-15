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

export interface ProductVariantInput {
  name: string;
  sku?: string | null;
  barcode?: string | null;
  price_cents?: number | null;
  promo_price_cents?: number | null;
  stock_quantity?: number;
}

export interface CatalogItemInput {
  name: string;
  description?: string | null;
  price_cents: number;
  kind: CatalogItemKind;
  tracks_inventory: boolean;
  stock_quantity?: number | null;
  sku?: string | null;
  barcode?: string | null;
  brand?: string | null;
  supplier?: string | null;
  category?: string | null;
  subcategory?: string | null;
  short_description?: string | null;
  tags?: string[];
  cost_price_cents?: number | null;
  promo_price_cents?: number | null;
  min_stock?: number | null;
  max_stock?: number | null;
  stock_location?: string | null;
  images?: string[];
  variants?: ProductVariantInput[];
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

export function useUpdateCatalogItem(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: { itemId: string } & Partial<CatalogItemInput>) => {
      const { itemId, ...payload } = input;
      const { data } = await api.patch<CatalogItemResponse>(
        `/companies/${companyId}/catalog-items/${itemId}`,
        payload,
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
