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

export interface UpdateCompanyInput {
  name?: string;
  brand_logo?: string | null;
  brand_primary_color?: string | null;
  brand_theme?: "light" | "dark" | null;
}

export function useUpdateCompany(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: UpdateCompanyInput) => {
      const { data } = await api.patch<CompanyResponse>(`/companies/${companyId}`, input);
      return data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["companies", companyId], data);
      void queryClient.invalidateQueries({ queryKey: ["companies"] });
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
