import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  ChangePlanRequest,
  CheckoutRequest,
  CheckoutResponse,
  PlanCatalogResponse,
  PlanResponse,
  SubscriptionResponse,
} from "@/lib/api-types";

export function usePlans() {
  return useQuery({
    queryKey: ["plans"],
    queryFn: async () => {
      const { data } = await api.get<PlanCatalogResponse>("/plans");
      return data.plans;
    },
    staleTime: 1000 * 60 * 60, // catálogo é estático
  });
}

export function useSubscription(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "subscription"],
    queryFn: async () => {
      const { data } = await api.get<SubscriptionResponse>(`/companies/${companyId}/subscription`);
      return data;
    },
  });
}

function invalidateSubscription(
  queryClient: ReturnType<typeof useQueryClient>,
  companyId: string,
): void {
  void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "subscription"] });
}

export function useChangePlan(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: ChangePlanRequest) => {
      const { data } = await api.put<SubscriptionResponse>(
        `/companies/${companyId}/subscription`,
        input,
      );
      return data;
    },
    onSuccess: () => invalidateSubscription(queryClient, companyId),
  });
}

/**
 * Contratação de plano pago.
 *
 * Não muda o plano: cria a cobrança no provedor e devolve o link de pagamento.
 * Quem libera o plano é o webhook, quando o dinheiro entra — por isso a
 * assinatura continua pendente até lá, mesmo depois desta chamada dar certo.
 */
export function useStartCheckout(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: CheckoutRequest) => {
      const { data } = await api.post<CheckoutResponse>(
        `/companies/${companyId}/billing/checkout`,
        input,
      );
      return data;
    },
    onSuccess: () => invalidateSubscription(queryClient, companyId),
  });
}

export function useCancelSubscription(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.delete<SubscriptionResponse>(
        `/companies/${companyId}/subscription`,
      );
      return data;
    },
    onSuccess: () => invalidateSubscription(queryClient, companyId),
  });
}

export type { PlanResponse };
