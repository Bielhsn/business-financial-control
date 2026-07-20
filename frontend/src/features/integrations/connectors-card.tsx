import { Link2, Plug, RefreshCw, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  useAvailableConnectors,
  useConnectProvider,
  useConnections,
  useDisconnectProvider,
  useSyncProvider,
} from "@/features/integrations/use-connectors";
import { extractErrorMessage } from "@/lib/api";
import type { ConnectionResponse, ConnectorDefinitionResponse } from "@/lib/api-types";

function ConnectDialog({
  companyId,
  connector,
}: {
  companyId: string;
  connector: ConnectorDefinitionResponse;
}) {
  const [open, setOpen] = useState(false);
  const [values, setValues] = useState<Record<string, string>>({});
  const connect = useConnectProvider(companyId);

  const submit = () => {
    for (const field of connector.credential_fields) {
      if (!values[field.key]?.trim()) {
        toast.error(`Informe ${field.label}.`);
        return;
      }
    }
    connect.mutate(
      { provider: connector.provider, credentials: values },
      {
        onSuccess: () => {
          toast.success(`${connector.name} conectada!`);
          setValues({});
          setOpen(false);
        },
        onError: (error) => toast.error(extractErrorMessage(error)),
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Link2 /> Conectar
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Conectar {connector.name}</DialogTitle>
          <DialogDescription>{connector.description}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          {connector.credential_fields.map((field) => (
            <div key={field.key} className="space-y-2">
              <Label htmlFor={`cred-${field.key}`}>{field.label}</Label>
              <Input
                id={`cred-${field.key}`}
                type={field.secret ? "password" : "text"}
                autoComplete="off"
                value={values[field.key] ?? ""}
                onChange={(event) =>
                  setValues((current) => ({ ...current, [field.key]: event.target.value }))
                }
              />
              {field.help_text && (
                <p className="text-xs text-muted-foreground">{field.help_text}</p>
              )}
            </div>
          ))}
          <p className="text-xs text-muted-foreground">
            As credenciais são validadas na hora e guardadas criptografadas. Nunca aparecem de volta
            na tela.
          </p>
        </div>
        <DialogFooter>
          <Button onClick={submit} disabled={connect.isPending}>
            {connect.isPending ? "Conectando…" : "Conectar e validar"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ConnectedRow({
  companyId,
  connector,
  connection,
}: {
  companyId: string;
  connector: ConnectorDefinitionResponse;
  connection: ConnectionResponse;
}) {
  const sync = useSyncProvider(companyId);
  const disconnect = useDisconnectProvider(companyId);

  const runSync = () =>
    sync.mutate(connector.provider, {
      onSuccess: (result) =>
        toast.success(
          `${connector.name}: ${result.imported} importado(s), ${result.skipped} já existiam.`,
        ),
      onError: (error) => toast.error(extractErrorMessage(error)),
    });

  const runDisconnect = () =>
    disconnect.mutate(connector.provider, {
      onSuccess: () => toast.success(`${connector.name} desconectada.`),
      onError: (error) => toast.error(extractErrorMessage(error)),
    });

  return (
    <div className="rounded-lg border p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <p className="flex items-center gap-2 text-sm font-medium">
            {connector.name}
            {connection.status === "connected" ? (
              <Badge variant="success">Conectada</Badge>
            ) : (
              <Badge variant="destructive">Erro</Badge>
            )}
          </p>
          <p className="text-xs text-muted-foreground">
            {connection.last_synced_at
              ? `Última sincronização: ${new Date(connection.last_synced_at).toLocaleString("pt-BR")}`
              : "Ainda não sincronizada."}
          </p>
        </div>
        <div className="flex items-center gap-1">
          <Button size="sm" variant="secondary" onClick={runSync} disabled={sync.isPending}>
            <RefreshCw className={sync.isPending ? "animate-spin" : ""} />
            {sync.isPending ? "Sincronizando…" : "Sincronizar agora"}
          </Button>
          <Button
            size="icon-sm"
            variant="ghost"
            aria-label={`Desconectar ${connector.name}`}
            onClick={runDisconnect}
            disabled={disconnect.isPending}
          >
            <Trash2 />
          </Button>
        </div>
      </div>
      {connection.status === "error" && connection.last_error && (
        <p className="mt-2 text-xs text-destructive">{connection.last_error}</p>
      )}
    </div>
  );
}

export function ConnectorsCard({ companyId }: { companyId: string }) {
  const { data: connectors } = useAvailableConnectors(companyId);
  const { data: connections } = useConnections(companyId);

  if (!connectors || connectors.length === 0) {
    return null;
  }

  const connectionByProvider = new Map((connections ?? []).map((c) => [c.provider, c]));

  return (
    <Card className="border-primary/40">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Plug className="size-4 text-primary" /> Conexões automáticas
        </CardTitle>
        <CardDescription>
          Conecte a conta e sincronize vendas e reembolsos direto no seu financeiro — sem digitar
          nada à mão.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {connectors.map((connector) => {
          const connection = connectionByProvider.get(connector.provider);
          if (connection) {
            return (
              <ConnectedRow
                key={connector.provider}
                companyId={companyId}
                connector={connector}
                connection={connection}
              />
            );
          }
          return (
            <div
              key={connector.provider}
              className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium">{connector.name}</p>
                <p className="text-xs text-muted-foreground">{connector.description}</p>
              </div>
              <ConnectDialog companyId={companyId} connector={connector} />
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
