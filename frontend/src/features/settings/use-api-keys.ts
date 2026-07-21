import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { ApiKeyResponse, CreatedApiKeyResponse } from "@/lib/api-types";

export function useApiKeys(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "api-keys"],
    queryFn: async () => {
      const { data } = await api.get<ApiKeyResponse[]>(`/companies/${companyId}/api-keys`);
      return data;
    },
  });
}

export function useCreateApiKey(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (name: string) => {
      const { data } = await api.post<CreatedApiKeyResponse>(`/companies/${companyId}/api-keys`, {
        name,
      });
      return data;
    },
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["companies", companyId, "api-keys"] }),
  });
}

export function useRevokeApiKey(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (keyId: string) => {
      await api.delete(`/companies/${companyId}/api-keys/${keyId}`);
    },
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["companies", companyId, "api-keys"] }),
  });
}
