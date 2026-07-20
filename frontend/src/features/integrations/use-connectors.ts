import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  ConnectionResponse,
  ConnectorDefinitionResponse,
  SyncResultResponse,
} from "@/lib/api-types";

export function useAvailableConnectors(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "connectors", "available"],
    queryFn: async () => {
      const { data } = await api.get<{ connectors: ConnectorDefinitionResponse[] }>(
        `/companies/${companyId}/connectors/available`,
      );
      return data.connectors;
    },
  });
}

export function useConnections(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "connectors", "connections"],
    queryFn: async () => {
      const { data } = await api.get<ConnectionResponse[]>(
        `/companies/${companyId}/connectors/connections`,
      );
      return data;
    },
  });
}

export function useConnectProvider(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: { provider: string; credentials: Record<string, string> }) => {
      const { data } = await api.post<ConnectionResponse>(
        `/companies/${companyId}/connectors/connect`,
        input,
      );
      return data;
    },
    onSuccess: () => invalidateConnections(queryClient, companyId),
  });
}

/** Inicia o fluxo OAuth: busca a URL de autorização e redireciona o navegador
 * para o provedor. `shop` é exigido pelo Shopify. */
export function useOAuthAuthorize(companyId: string) {
  return useMutation({
    mutationFn: async (input: { provider: string; shop?: string }) => {
      const { data } = await api.get<{ authorize_url: string }>(
        `/companies/${companyId}/connectors/${input.provider}/oauth/authorize`,
        { params: input.shop ? { shop: input.shop } : undefined },
      );
      return data.authorize_url;
    },
    onSuccess: (authorizeUrl) => {
      window.location.href = authorizeUrl;
    },
  });
}

export function useSyncProvider(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (provider: string) => {
      const { data } = await api.post<SyncResultResponse>(
        `/companies/${companyId}/connectors/${provider}/sync`,
      );
      return data;
    },
    onSuccess: () => {
      void invalidateConnections(queryClient, companyId);
      // O sync cria lançamentos — dashboard e financeiro precisam recarregar.
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "transactions"] });
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "dashboard"] });
    },
  });
}

export function useDisconnectProvider(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (provider: string) => {
      await api.delete(`/companies/${companyId}/connectors/${provider}`);
    },
    onSuccess: () => invalidateConnections(queryClient, companyId),
  });
}

function invalidateConnections(
  queryClient: ReturnType<typeof useQueryClient>,
  companyId: string,
): Promise<void> {
  return queryClient.invalidateQueries({
    queryKey: ["companies", companyId, "connectors", "connections"],
  });
}
