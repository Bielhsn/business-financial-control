import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  CnpjLookupResponse,
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
  legal_name?: string | null;
  trade_name?: string | null;
  cnpj?: string | null;
  subsegment?: string | null;
  monthly_revenue_cents?: number | null;
  phone?: string | null;
  email?: string | null;
  website?: string | null;
  social_links?: Record<string, string>;
}

/** Consulta um CNPJ (apenas dígitos) na Receita via backend, para autopreencher. */
export function useLookupCnpj() {
  return useMutation({
    mutationFn: async (cnpj: string) => {
      const digits = cnpj.replace(/\D/g, "");
      const { data } = await api.get<CnpjLookupResponse>(`/cnpj/${digits}`);
      return data;
    },
  });
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
