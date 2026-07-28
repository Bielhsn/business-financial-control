import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { DEFAULT_PAGE_SIZE } from "@/components/ui/pagination";
import { api } from "@/lib/api";
import type {
  Page,
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

/**
 * Lançamentos paginados no servidor.
 *
 * É a coleção que mais cresce — uma loja com anos de histórico tem milhares de
 * linhas. Buscar tudo para desenhar cinco desperdiça banda e memória do
 * navegador, então a página vai como parâmetro e o total volta junto para a
 * interface saber quantas páginas existem.
 *
 * `placeholderData` mantém a página anterior na tela durante a troca: sem isso
 * a lista pisca em branco a cada clique na paginação.
 */
export function useTransactions(
  companyId: string,
  filters: TransactionFilters = {},
  page: { limit: number; offset: number } = { limit: DEFAULT_PAGE_SIZE, offset: 0 },
) {
  const params = { ...filters, limit: page.limit, offset: page.offset };
  return useQuery({
    queryKey: ["companies", companyId, "transactions", params],
    queryFn: async () => {
      const { data } = await api.get<Page<FinancialTransactionResponse>>(
        `/companies/${companyId}/transactions`,
        { params },
      );
      return data;
    },
    placeholderData: (previous) => previous,
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
      // Uma receita paga com cliente atualiza a última visita dele no backend.
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "clients"] });
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
      // Receber de um cliente atualiza a última visita dele no backend.
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "clients"] });
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
