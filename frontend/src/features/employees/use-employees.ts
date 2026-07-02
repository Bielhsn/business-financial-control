import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { EmployeeResponse } from "@/lib/api-types";

export function useEmployees(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "employees"],
    queryFn: async () => {
      const { data } = await api.get<EmployeeResponse[]>(`/companies/${companyId}/employees`);
      return data;
    },
  });
}

export interface EmployeeInput {
  name: string;
  email?: string | null;
  phone?: string | null;
  role_title?: string | null;
}

export function useCreateEmployee(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: EmployeeInput) => {
      const { data } = await api.post<EmployeeResponse>(`/companies/${companyId}/employees`, input);
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "employees"] });
    },
  });
}
