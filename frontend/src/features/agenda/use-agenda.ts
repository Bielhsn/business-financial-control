import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { AppointmentResponse, AppointmentStatus } from "@/lib/api-types";

export function useAppointments(companyId: string, start: string, end: string) {
  return useQuery({
    queryKey: ["companies", companyId, "appointments", start, end],
    queryFn: async () => {
      const { data } = await api.get<AppointmentResponse[]>(
        `/companies/${companyId}/appointments`,
        { params: { start, end } },
      );
      return data;
    },
  });
}

export interface AppointmentInput {
  title?: string | null;
  starts_at: string;
  duration_minutes: number;
  client_id?: string | null;
  employee_id?: string | null;
  catalog_item_id?: string | null;
  price_cents?: number | null;
  notes?: string | null;
}

export function useCreateAppointment(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: AppointmentInput) => {
      const { data } = await api.post<AppointmentResponse>(
        `/companies/${companyId}/appointments`,
        input,
      );
      return data;
    },
    onSuccess: () => invalidate(queryClient, companyId),
  });
}

export function useUpdateAppointment(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: { id: string } & Partial<AppointmentInput>) => {
      const { id, ...payload } = input;
      const { data } = await api.patch<AppointmentResponse>(
        `/companies/${companyId}/appointments/${id}`,
        payload,
      );
      return data;
    },
    onSuccess: () => invalidate(queryClient, companyId),
  });
}

export function useChangeAppointmentStatus(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: { id: string; status: AppointmentStatus }) => {
      const { data } = await api.post<AppointmentResponse>(
        `/companies/${companyId}/appointments/${input.id}/status`,
        { status: input.status },
      );
      return data;
    },
    onSuccess: () => {
      void invalidate(queryClient, companyId);
      // Concluir gera receita — o dashboard/financeiro precisam recarregar.
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "transactions"] });
      void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "dashboard"] });
    },
  });
}

function invalidate(
  queryClient: ReturnType<typeof useQueryClient>,
  companyId: string,
): Promise<void> {
  return queryClient.invalidateQueries({
    queryKey: ["companies", companyId, "appointments"],
  });
}
