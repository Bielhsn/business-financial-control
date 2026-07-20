import { Mail, Trash2, UserPlus, Users } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  useChangeMemberRole,
  useInviteMember,
  useInvitations,
  useMembers,
  useRemoveMember,
  useRevokeInvitation,
} from "@/features/settings/use-team";
import { extractErrorMessage } from "@/lib/api";
import type { CompanyRole } from "@/lib/api-types";

// Papéis atribuíveis (owner não é convidável; a transferência de posse é à parte).
const ASSIGNABLE_ROLES: CompanyRole[] = ["admin", "manager", "employee", "viewer"];

const ROLE_LABELS: Record<CompanyRole, string> = {
  owner: "Proprietário",
  admin: "Administrador",
  manager: "Gerente",
  employee: "Funcionário",
  viewer: "Visualizador",
};

export function TeamCard({ companyId }: { companyId: string }) {
  const { data: members } = useMembers(companyId);
  const { data: invitations } = useInvitations(companyId);
  const invite = useInviteMember(companyId);
  const changeRole = useChangeMemberRole(companyId);
  const removeMember = useRemoveMember(companyId);
  const revoke = useRevokeInvitation(companyId);

  const [email, setEmail] = useState("");
  const [role, setRole] = useState<CompanyRole>("employee");

  const handleInvite = () => {
    if (!email.trim()) {
      toast.error("Informe o e-mail de quem você quer convidar.");
      return;
    }
    invite.mutate(
      { email: email.trim(), role },
      {
        onSuccess: (result) => {
          toast.success(
            result === null
              ? "Usuário já tinha conta e foi adicionado à equipe!"
              : "Convite enviado por e-mail!",
          );
          setEmail("");
        },
        onError: (error) => toast.error(extractErrorMessage(error)),
      },
    );
  };

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Users className="size-4 text-primary" /> Equipe
        </CardTitle>
        <CardDescription>
          Convide pessoas e defina o que cada uma pode fazer. Proprietários e administradores
          gerenciam a equipe.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Convidar */}
        <div className="flex flex-wrap items-end gap-2">
          <div className="min-w-48 flex-1 space-y-2">
            <Label htmlFor="invite-email">Convidar por e-mail</Label>
            <Input
              id="invite-email"
              type="email"
              placeholder="pessoa@empresa.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Papel</Label>
            <Select value={role} onValueChange={(value) => setRole(value as CompanyRole)}>
              <SelectTrigger className="w-40" aria-label="Papel do convidado">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ASSIGNABLE_ROLES.map((r) => (
                  <SelectItem key={r} value={r}>
                    {ROLE_LABELS[r]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button onClick={handleInvite} disabled={invite.isPending}>
            <UserPlus /> {invite.isPending ? "Enviando…" : "Convidar"}
          </Button>
        </div>

        {/* Membros */}
        <div className="space-y-2">
          <p className="text-sm font-medium">Membros ({members?.length ?? 0})</p>
          <ul className="divide-y rounded-lg border">
            {(members ?? []).map((member) => (
              <li
                key={member.user_id}
                className="flex flex-wrap items-center justify-between gap-2 p-3"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{member.full_name}</p>
                  <p className="truncate text-xs text-muted-foreground">{member.email}</p>
                </div>
                <div className="flex items-center gap-2">
                  {member.role === "owner" ? (
                    <Badge variant="secondary">Proprietário</Badge>
                  ) : (
                    <Select
                      value={member.role}
                      onValueChange={(value) =>
                        changeRole.mutate(
                          { userId: member.user_id, role: value as CompanyRole },
                          { onError: (e) => toast.error(extractErrorMessage(e)) },
                        )
                      }
                    >
                      <SelectTrigger
                        className="h-8 w-36"
                        aria-label={`Papel de ${member.full_name}`}
                      >
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {ASSIGNABLE_ROLES.map((r) => (
                          <SelectItem key={r} value={r}>
                            {ROLE_LABELS[r]}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                  {member.role !== "owner" && (
                    <Button
                      size="icon-sm"
                      variant="ghost"
                      aria-label={`Remover ${member.full_name}`}
                      onClick={() =>
                        removeMember.mutate(member.user_id, {
                          onSuccess: () => toast.success("Membro removido."),
                          onError: (e) => toast.error(extractErrorMessage(e)),
                        })
                      }
                    >
                      <Trash2 />
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Convites pendentes */}
        {(invitations?.length ?? 0) > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Convites pendentes</p>
            <ul className="divide-y rounded-lg border">
              {(invitations ?? []).map((inv) => (
                <li key={inv.id} className="flex items-center justify-between gap-2 p-3">
                  <div className="flex min-w-0 items-center gap-2">
                    <Mail className="size-4 shrink-0 text-muted-foreground" />
                    <div className="min-w-0">
                      <p className="truncate text-sm">{inv.email}</p>
                      <p className="text-xs text-muted-foreground">{ROLE_LABELS[inv.role]}</p>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() =>
                      revoke.mutate(inv.id, {
                        onSuccess: () => toast.success("Convite revogado."),
                        onError: (e) => toast.error(extractErrorMessage(e)),
                      })
                    }
                  >
                    Revogar
                  </Button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
