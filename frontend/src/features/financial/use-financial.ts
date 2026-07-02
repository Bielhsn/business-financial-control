import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  FinancialCategoryResponse,
  FinancialCategoryType,
  FinancialTransactionResponse,
  TransactionStatus,
} from "@/lib/api-types";

export function useCategories(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "categories"],
    queryFn: async () => {
      const { data } = await api.get<FinancialCategoryResponse[]>(
        `/companies/${companyId}/financial-categories`,
      );
      return data;
    },
  });
}

export function useCreateCategory(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: { name: string; type: FinancialCategoryType }) => {
      const { data } = await api.post<FinancialCategoryResponse>(
        `/companies/${companyId}/financial-categories`,
        input,
      );
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "categories"] });
    },
  });
}

export interface TransactionFilters {
  type?: FinancialCategoryType;
  status?: TransactionStatus;
}

export function useTransactions(companyId: string, filters: TransactionFilters = {}) {
  return useQuery({
    queryKey: ["companies", companyId, "transactions", filters],
    queryFn: async () => {
      const { data } = await api.get<FinancialTransactionResponse[]>(
        `/companies/${companyId}/transactions`,
        { params: filters },
      );
      return data;
    },
  });
}

export interface CreateTransactionInput {
  category_id: string;
  type: FinancialCategoryType;
  amount_cents: number;
  description: string;
  due_date?: string | null;
  paid_at?: string | null;
  notes?: string | null;
  client_id?: string | null;
}

export function useCreateTransaction(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: CreateTransactionInput) => {
      const { data } = await api.post<FinancialTransactionResponse>(
        `/companies/${companyId}/transactions`,
        input,
      );
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "transactions"] });
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "dashboard"] });
    },
  });
}

export function useMarkTransactionPaid(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (transactionId: string) => {
      const { data } = await api.post<FinancialTransactionResponse>(
        `/companies/${companyId}/transactions/${transactionId}/mark-paid`,
        {},
      );
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "transactions"] });
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "dashboard"] });
    },
  });
}

export function useCancelTransaction(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (transactionId: string) => {
      const { data } = await api.post<FinancialTransactionResponse>(
        `/companies/${companyId}/transactions/${transactionId}/cancel`,
      );
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "transactions"] });
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "dashboard"] });
    },
  });
}
