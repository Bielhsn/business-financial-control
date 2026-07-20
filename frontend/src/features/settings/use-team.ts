import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { CompanyRole, InvitationResponse, MemberResponse } from "@/lib/api-types";

export function useMembers(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "members"],
    queryFn: async () => {
      const { data } = await api.get<MemberResponse[]>(`/companies/${companyId}/members`);
      return data;
    },
  });
}

export function useInvitations(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "invitations"],
    queryFn: async () => {
      const { data } = await api.get<InvitationResponse[]>(`/companies/${companyId}/invitations`);
      return data;
    },
  });
}

function invalidateTeam(queryClient: ReturnType<typeof useQueryClient>, companyId: string): void {
  void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "members"] });
  void queryClient.invalidateQueries({ queryKey: ["companies", companyId, "invitations"] });
}

export function useInviteMember(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: { email: string; role: CompanyRole }) => {
      const { data } = await api.post<InvitationResponse | null>(
        `/companies/${companyId}/invitations`,
        input,
      );
      return data;
    },
    onSuccess: () => invalidateTeam(queryClient, companyId),
  });
}

export function useChangeMemberRole(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: { userId: string; role: CompanyRole }) => {
      const { data } = await api.patch<MemberResponse>(
        `/companies/${companyId}/members/${input.userId}`,
        { role: input.role },
      );
      return data;
    },
    onSuccess: () => invalidateTeam(queryClient, companyId),
  });
}

export function useRemoveMember(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (userId: string) => {
      await api.delete(`/companies/${companyId}/members/${userId}`);
    },
    onSuccess: () => invalidateTeam(queryClient, companyId),
  });
}

export function useRevokeInvitation(companyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (invitationId: string) => {
      await api.delete(`/companies/${companyId}/invitations/${invitationId}`);
    },
    onSuccess: () => invalidateTeam(queryClient, companyId),
  });
}

export function useExportCompanyData(companyId: string) {
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.get<Record<string, unknown>>(`/companies/${companyId}/export`);
      return data;
    },
  });
}

export function useDeleteCompany(companyId: string) {
  return useMutation({
    mutationFn: async () => {
      await api.delete(`/companies/${companyId}`);
    },
  });
}
