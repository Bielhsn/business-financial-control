import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { ClientResponse, ClientSummaryResponse } from "@/lib/api-types";

export function useClients(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "clients"],
    queryFn: async () => {
      const { data } = await api.get<ClientResponse[]>(`/companies/${companyId}/clients`);
      return data;
    },
  });
}

export function useClientSummary(companyId: string, clientId: string | null) {
  return useQuery({
    queryKey: ["companies", companyId, "clients", clientId, "summary"],
    queryFn: async () => {
      const { data } = await api.get<ClientSummaryResponse>(
        `/companies/${companyId}/clients/${clientId}/summary`,
      );
      return data;
    },
    enabled: clientId !== null,
  });
}

export interface ClientInput {
  name: string;
  email?: string | null;
  phone?: string | null;
  notes?: string | null;
  custom_fields: Record<string, string>;
}

export function useCreateClient(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: ClientInput) => {
      const { data } = await api.post<ClientResponse>(`/companies/${companyId}/clients`, input);
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "clients"] });
    },
  });
}

export function useUpdateClient(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ clientId, ...input }: ClientInput & { clientId: string }) => {
      const { data } = await api.patch<ClientResponse>(
        `/companies/${companyId}/clients/${clientId}`,
        input,
      );
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "clients"] });
    },
  });
}
