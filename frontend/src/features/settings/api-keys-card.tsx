import { Copy, KeyRound, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useApiKeys, useCreateApiKey, useRevokeApiKey } from "@/features/settings/use-api-keys";
import { extractErrorMessage } from "@/lib/api";

export function ApiKeysCard({ companyId }: { companyId: string }) {
  const { data: keys } = useApiKeys(companyId);
  const createKey = useCreateApiKey(companyId);
  const revokeKey = useRevokeApiKey(companyId);
  const [name, setName] = useState("");
  const [newKey, setNewKey] = useState<string | null>(null);

  const create = () => {
    if (!name.trim()) {
      toast.error("Dê um nome para a chave.");
      return;
    }
    createKey.mutate(name.trim(), {
      onSuccess: (data) => {
        setNewKey(data.raw_key);
        setName("");
        toast.success("Chave criada. Copie agora — ela não aparecerá de novo.");
      },
      onError: (error) => toast.error(extractErrorMessage(error)),
    });
  };

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <KeyRound className="size-4" /> Chaves de API
        </CardTitle>
        <CardDescription>
          Acesso programático à API pública (recurso do plano Enterprise). Autentique com o header{" "}
          <code className="rounded bg-muted px-1">X-API-Key</code>.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {newKey && (
          <div className="space-y-2 rounded-lg border border-primary/40 bg-primary/5 p-3">
            <p className="text-sm font-medium">Sua nova chave (copie agora):</p>
            <div className="flex items-center gap-2">
              <code className="min-w-0 flex-1 truncate rounded bg-background px-2 py-1 text-xs">
                {newKey}
              </code>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  void navigator.clipboard.writeText(newKey);
                  toast.success("Chave copiada.");
                }}
              >
                <Copy /> Copiar
              </Button>
            </div>
          </div>
        )}

        <div className="flex flex-wrap items-center gap-2">
          <Input
            className="max-w-xs"
            placeholder="Nome da chave (ex.: Integração ERP)"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
          <Button onClick={create} disabled={createKey.isPending}>
            <Plus /> {createKey.isPending ? "Criando…" : "Criar chave"}
          </Button>
        </div>

        <div className="space-y-2">
          {(keys ?? []).length === 0 && (
            <p className="text-sm text-muted-foreground">Nenhuma chave criada ainda.</p>
          )}
          {(keys ?? []).map((key) => (
            <div
              key={key.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3"
            >
              <div className="min-w-0">
                <p className="flex items-center gap-2 text-sm font-medium">
                  {key.name}
                  {key.revoked && <Badge variant="destructive">Revogada</Badge>}
                </p>
                <p className="text-xs text-muted-foreground">
                  <code>{key.prefix}…</code> ·{" "}
                  {key.last_used_at
                    ? `último uso ${new Date(key.last_used_at).toLocaleDateString("pt-BR")}`
                    : "nunca usada"}
                </p>
              </div>
              {!key.revoked && (
                <Button
                  variant="ghost"
                  size="icon-sm"
                  aria-label={`Revogar ${key.name}`}
                  onClick={() =>
                    revokeKey.mutate(key.id, {
                      onSuccess: () => toast.success("Chave revogada."),
                      onError: (error) => toast.error(extractErrorMessage(error)),
                    })
                  }
                  disabled={revokeKey.isPending}
                >
                  <Trash2 />
                </Button>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
