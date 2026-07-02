import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  CompanyResponse,
  CompanyWithRoleResponse,
  CreateCompanyRequest,
} from "@/lib/api-types";

export function useMyCompanies() {
  return useQuery({
    queryKey: ["companies"],
    queryFn: async () => {
      const { data } = await api.get<CompanyWithRoleResponse[]>("/companies");
      return data;
    },
  });
}

export function useCompany(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId],
    queryFn: async () => {
      const { data } = await api.get<CompanyResponse>(`/companies/${companyId}`);
      return data;
    },
  });
}

export function useCreateCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: CreateCompanyRequest) => {
      const { data } = await api.post<CompanyResponse>("/companies", input);
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["companies"] });
    },
  });
}
