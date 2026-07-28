/**
 * Ações de uma integração, no estado real da conexão.
 *
 * Antes existiam dois mundos: um cartão "Conexões automáticas" com botões que
 * funcionavam, e as listas de recomendadas/catálogo que só desenhavam um selo
 * "Disponível" sem nada para clicar. Quem via a recomendação para o seu segmento
 * não tinha como agir sobre ela.
 *
 * Aqui a decisão é uma só e vale para qualquer lugar que liste integrações:
 *
 *   sem conector          → diz que ainda não conecta, sem prometer botão
 *   conector, sem conexão → "Conectar" abre o fluxo certo (credenciais ou OAuth)
 *   conectada             → "Sincronizar" e "Desconectar", com o status real
 *
 * O estado vem das conexões persistidas no backend, não de um rótulo fixo.
 */
import { Link2, RefreshCw, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
  useConnectProvider,
  useDisconnectProvider,
  useOAuthAuthorize,
  useSyncProvider,
} from "@/features/integrations/use-connectors";
import { extractErrorMessage } from "@/lib/api";
import type { ConnectionResponse, ConnectorDefinitionResponse } from "@/lib/api-types";

/** Conexão por credenciais: o lojista cola as chaves do aplicativo dele. */
function CredentialsConnectDialog({
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
              <Label htmlFor={`cred-${connector.provider}-${field.key}`}>{field.label}</Label>
              <Input
                id={`cred-${connector.provider}-${field.key}`}
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

/** Conexão por OAuth: redireciona o lojista para autorizar no provedor. */
function OAuthConnectButton({
  companyId,
  connector,
}: {
  companyId: string;
  connector: ConnectorDefinitionResponse;
}) {
  const [open, setOpen] = useState(false);
  const [shop, setShop] = useState("");
  const authorize = useOAuthAuthorize(companyId);
  // A Shopify precisa saber qual loja autorizar antes do redirect.
  const needsShop = connector.provider === "shopify";

  const start = (payload: { provider: string; shop?: string }) =>
    authorize.mutate(payload, {
      // onSuccess redireciona o navegador; só tratamos erro aqui.
      onError: (error) => toast.error(extractErrorMessage(error)),
    });

  if (!needsShop) {
    return (
      <Button
        size="sm"
        onClick={() => start({ provider: connector.provider })}
        disabled={authorize.isPending}
      >
        <Link2 /> {authorize.isPending ? "Autorizando…" : "Conectar"}
      </Button>
    );
  }

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
          <DialogDescription>
            Informe o endereço da sua loja para autorizar o acesso.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <Label htmlFor="shop-domain">Loja</Label>
          <div className="flex items-center gap-2">
            <Input
              id="shop-domain"
              placeholder="minha-loja"
              value={shop}
              onChange={(event) => setShop(event.target.value.trim())}
            />
            <span className="text-sm text-muted-foreground">.myshopify.com</span>
          </div>
        </div>
        <DialogFooter>
          <Button
            onClick={() => {
              if (!shop) {
                toast.error("Informe o endereço da loja.");
                return;
              }
              start({ provider: connector.provider, shop });
            }}
            disabled={authorize.isPending}
          >
            {authorize.isPending ? "Autorizando…" : "Autorizar"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/** Conexão ativa: sincronizar sob demanda ou desfazer. */
function ConnectedActions({
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

  return (
    <div className="flex items-center gap-1">
      <Button
        size="sm"
        variant="secondary"
        onClick={() =>
          sync.mutate(connector.provider, {
            onSuccess: (result) =>
              toast.success(
                `${connector.name}: ${result.imported} importado(s), ${result.skipped} já existiam.`,
              ),
            onError: (error) => toast.error(extractErrorMessage(error)),
          })
        }
        disabled={sync.isPending}
      >
        <RefreshCw className={sync.isPending ? "animate-spin" : ""} />
        {sync.isPending ? "Sincronizando…" : "Sincronizar"}
      </Button>
      <Button
        size="icon-sm"
        variant="ghost"
        aria-label={`Desconectar ${connector.name}`}
        onClick={() =>
          disconnect.mutate(connector.provider, {
            onSuccess: () => toast.success(`${connector.name} desconectada.`),
            onError: (error) => toast.error(extractErrorMessage(error)),
          })
        }
        disabled={disconnect.isPending}
      >
        <Trash2 />
      </Button>
      {connection.status === "error" && <Badge variant="destructive">Erro</Badge>}
    </div>
  );
}

export function IntegrationActions({
  companyId,
  connector,
  connection,
}: {
  companyId: string;
  /** Ausente quando a plataforma ainda não tem conector implementado. */
  connector: ConnectorDefinitionResponse | undefined;
  connection: ConnectionResponse | undefined;
}) {
  // Sem conector, ser honesto vale mais que um selo bonito: prometer
  // "Disponível" para algo que não conecta é o defeito que estamos corrigindo.
  if (!connector) {
    return (
      <Badge variant="muted" title="Ainda não há conexão automática para esta plataforma">
        Sem conexão automática
      </Badge>
    );
  }
  if (connection) {
    return <ConnectedActions companyId={companyId} connector={connector} connection={connection} />;
  }
  return connector.auth_type === "oauth" ? (
    <OAuthConnectButton companyId={companyId} connector={connector} />
  ) : (
    <CredentialsConnectDialog companyId={companyId} connector={connector} />
  );
}

/** Selo do estado atual, para acompanhar as ações na listagem. */
export function IntegrationStatusBadge({
  connector,
  connection,
}: {
  connector: ConnectorDefinitionResponse | undefined;
  connection: ConnectionResponse | undefined;
}) {
  if (connection) {
    return connection.status === "connected" ? (
      <Badge variant="success">Conectada</Badge>
    ) : (
      <Badge variant="destructive">Erro na conexão</Badge>
    );
  }
  if (connector) {
    return <Badge variant="secondary">Pronta para conectar</Badge>;
  }
  return null;
}
