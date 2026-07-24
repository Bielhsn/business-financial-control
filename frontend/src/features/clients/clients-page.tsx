import { zodResolver } from "@hookform/resolvers/zod";
import { CalendarCheck, Clock, MessageCircle, Plus, ShoppingBag, Users } from "lucide-react";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { useParams } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useBlueprint } from "@/features/blueprint/use-blueprint";
import { useCompany } from "@/features/companies/use-companies";
import {
  useClientSummary,
  useClients,
  useCreateClient,
  useRegisterVisit,
  useSetReturnInterval,
} from "@/features/clients/use-clients";
import { extractErrorMessage } from "@/lib/api";
import type { BlueprintCustomField, ClientResponse } from "@/lib/api-types";
import { useCompanyCurrency } from "@/features/companies/use-company-currency";
import { computeReturnStatus } from "@/lib/client-return";
import { formatCents } from "@/lib/utils";
import { buildWhatsappLink } from "@/lib/whatsapp";

/** Opções de cadência de retorno oferecidas ao barbeiro/salão. */
const RETURN_INTERVAL_OPTIONS = [7, 10, 15, 21, 30, 45, 60];

const clientSchema = z.object({
  name: z.string().min(1, "Informe o nome do cliente.").max(200),
  email: z.string().email("E-mail inválido.").or(z.literal("")).optional(),
  phone: z.string().max(50).optional(),
  notes: z.string().max(2000).optional(),
  custom_fields: z.record(z.string()),
  return_interval_days: z.string().optional(),
});

type ClientForm = z.infer<typeof clientSchema>;

function CustomFieldInput({
  field,
  value,
  onChange,
}: {
  field: BlueprintCustomField;
  value: string;
  onChange: (value: string) => void;
}) {
  const id = `custom-${field.key}`;
  const inputType = field.type === "number" ? "number" : field.type === "date" ? "date" : "text";
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{field.label}</Label>
      <Input id={id} type={inputType} value={value} onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}

function NewClientDialog({ companyId }: { companyId: string }) {
  const [open, setOpen] = useState(false);
  const { data: blueprint } = useBlueprint(companyId);
  const createClient = useCreateClient(companyId);
  const customFieldDefs = blueprint?.client_custom_fields ?? [];

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<ClientForm>({
    resolver: zodResolver(clientSchema),
    defaultValues: { custom_fields: {} },
  });

  const customFields = watch("custom_fields");

  const onSubmit = handleSubmit((values) => {
    // Só envia campos personalizados preenchidos — chave vazia seria rejeitada pelo backend.
    const filledCustomFields = Object.fromEntries(
      Object.entries(values.custom_fields).filter(([, value]) => value.trim() !== ""),
    );
    const interval = values.return_interval_days ? Number(values.return_interval_days) : null;
    createClient.mutate(
      {
        name: values.name,
        email: values.email || null,
        phone: values.phone || null,
        notes: values.notes || null,
        custom_fields: filledCustomFields,
        return_interval_days: interval,
      },
      {
        onSuccess: () => {
          toast.success("Cliente cadastrado!");
          reset({ custom_fields: {} });
          setOpen(false);
        },
        onError: (error) => toast.error(extractErrorMessage(error)),
      },
    );
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus /> Novo cliente
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Novo cliente</DialogTitle>
          <DialogDescription>
            {customFieldDefs.length > 0
              ? "Os campos extras abaixo foram sugeridos pela IA para o seu segmento."
              : "Cadastre os dados básicos do cliente."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          <div className="space-y-2">
            <Label htmlFor="client-name">Nome</Label>
            <Input id="client-name" {...register("name")} />
            {errors.name && (
              <p role="alert" className="text-sm text-destructive">
                {errors.name.message}
              </p>
            )}
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="client-email">E-mail (opcional)</Label>
              <Input id="client-email" type="email" {...register("email")} />
              {errors.email && (
                <p role="alert" className="text-sm text-destructive">
                  {errors.email.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="client-phone">Telefone / WhatsApp (opcional)</Label>
              <Input id="client-phone" placeholder="(11) 99999-8888" {...register("phone")} />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="client-interval">Retorno esperado (opcional)</Label>
            <select
              id="client-interval"
              className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              {...register("return_interval_days")}
            >
              <option value="">Não lembrar</option>
              {RETURN_INTERVAL_OPTIONS.map((days) => (
                <option key={days} value={days}>
                  A cada {days} dias
                </option>
              ))}
            </select>
            <p className="text-xs text-muted-foreground">
              Usado para avisar quando o cliente está na hora de voltar (aba Retorno).
            </p>
          </div>

          {customFieldDefs.length > 0 && (
            <div className="grid gap-4 sm:grid-cols-2">
              {customFieldDefs.map((field) => (
                <CustomFieldInput
                  key={field.key}
                  field={field}
                  value={customFields[field.key] ?? ""}
                  onChange={(value) =>
                    setValue("custom_fields", { ...customFields, [field.key]: value })
                  }
                />
              ))}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="client-notes">Observações (opcional)</Label>
            <Textarea id="client-notes" {...register("notes")} />
          </div>

          <DialogFooter>
            <Button type="submit" disabled={createClient.isPending}>
              {createClient.isPending ? "Salvando…" : "Cadastrar cliente"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function ClientDetailDialog({
  client,
  companyId,
  customFieldDefs,
}: {
  client: ClientResponse;
  companyId: string;
  customFieldDefs: BlueprintCustomField[];
}) {
  const [open, setOpen] = useState(false);
  const currency = useCompanyCurrency(companyId);
  const { data: summary } = useClientSummary(companyId, open ? client.id : null);
  const labelFor = (key: string) =>
    customFieldDefs.find((field) => field.key === key)?.label ?? key;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <button
          type="button"
          className="w-full rounded-none border-b px-5 py-3 text-left transition-colors last:border-b-0 hover:bg-accent/40"
        >
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{client.name}</p>
              <p className="truncate text-xs text-muted-foreground">
                {[client.email, client.phone].filter(Boolean).join(" · ") || "Sem contato"}
              </p>
            </div>
            <ShoppingBag className="size-4 shrink-0 text-muted-foreground" />
          </div>
        </button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{client.name}</DialogTitle>
          <DialogDescription>Relacionamento com a empresa.</DialogDescription>
        </DialogHeader>
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-lg border p-3 text-center">
            <p className="text-xs text-muted-foreground">Total gasto</p>
            <p className="mt-1 text-sm font-semibold">
              {summary ? formatCents(summary.total_spent_cents, currency) : "…"}
            </p>
          </div>
          <div className="rounded-lg border p-3 text-center">
            <p className="text-xs text-muted-foreground">Compras</p>
            <p className="mt-1 text-sm font-semibold">{summary?.purchase_count ?? "…"}</p>
          </div>
          <div className="rounded-lg border p-3 text-center">
            <p className="text-xs text-muted-foreground">Última compra</p>
            <p className="mt-1 text-sm font-semibold">
              {summary
                ? summary.last_purchase_at
                  ? new Date(summary.last_purchase_at).toLocaleDateString("pt-BR")
                  : "—"
                : "…"}
            </p>
          </div>
        </div>
        {Object.keys(client.custom_fields).length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Campos do segmento</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(client.custom_fields).map(([key, value]) => (
                <Badge key={key} variant="secondary">
                  {labelFor(key)}: {value}
                </Badge>
              ))}
            </div>
          </div>
        )}
        {client.notes && <p className="text-sm text-muted-foreground">{client.notes}</p>}
      </DialogContent>
    </Dialog>
  );
}

function ReturnStatusBadge({ client }: { client: ClientResponse }) {
  const status = computeReturnStatus(client.last_visit_at, client.return_interval_days);
  if (!status.hasSchedule) {
    if (client.return_interval_days === null) {
      return <Badge variant="secondary">Sem cadência</Badge>;
    }
    return <Badge variant="secondary">Sem visita registrada</Badge>;
  }
  if (status.isDue) {
    const overdue = Math.abs(status.daysUntilDue ?? 0);
    return (
      <Badge variant="destructive">
        {overdue === 0 ? "Na hora de voltar" : `Atrasado ${overdue}d`}
      </Badge>
    );
  }
  return <Badge variant="secondary">Faltam {status.daysUntilDue}d</Badge>;
}

function ClientReturnCard({
  client,
  companyId,
  companyName,
}: {
  client: ClientResponse;
  companyId: string;
  companyName: string | undefined;
}) {
  const registerVisit = useRegisterVisit(companyId);
  const setInterval = useSetReturnInterval(companyId);

  const firstName = client.name.trim().split(" ")[0];
  const message = `Olá, ${firstName}! Tudo bem? Já faz um tempinho desde sua última visita${
    companyName ? ` na ${companyName}` : ""
  }. Que tal agendar seu retorno? 😊`;
  const waLink = buildWhatsappLink(client.phone, message);

  const lastVisit = client.last_visit_at
    ? new Date(client.last_visit_at).toLocaleDateString("pt-BR")
    : "—";

  return (
    <Card>
      <CardContent className="space-y-3 p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="truncate font-medium">{client.name}</p>
            {/* Telefone é a identidade real: dois clientes de mesmo nome se
                distinguem pelo número de contato. */}
            <p className="truncate text-sm text-muted-foreground">
              {client.phone || "Sem telefone"}
            </p>
          </div>
          <ReturnStatusBadge client={client} />
        </div>

        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Clock className="size-3.5" /> Última visita: {lastVisit}
          </span>
        </div>

        <div className="space-y-1">
          <Label className="text-xs text-muted-foreground">Retornar a cada</Label>
          <Select
            value={client.return_interval_days ? String(client.return_interval_days) : undefined}
            onValueChange={(value) =>
              setInterval.mutate({ clientId: client.id, days: Number(value) })
            }
          >
            <SelectTrigger className="h-8">
              <SelectValue placeholder="Definir cadência" />
            </SelectTrigger>
            <SelectContent>
              {RETURN_INTERVAL_OPTIONS.map((days) => (
                <SelectItem key={days} value={String(days)}>
                  {days} dias
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              registerVisit.mutate(client.id, {
                onSuccess: () => toast.success("Atendimento registrado!"),
                onError: (error) => toast.error(extractErrorMessage(error)),
              })
            }
            disabled={registerVisit.isPending}
          >
            <CalendarCheck className="size-4" /> Registrar atendimento
          </Button>
          {waLink ? (
            <Button asChild size="sm">
              <a href={waLink} target="_blank" rel="noopener noreferrer">
                <MessageCircle className="size-4" /> Chamar no WhatsApp
              </a>
            </Button>
          ) : (
            <Button size="sm" disabled title="Cadastre o telefone do cliente">
              <MessageCircle className="size-4" /> Sem telefone
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function ClientReturnView({
  clients,
  companyId,
  companyName,
}: {
  clients: ClientResponse[];
  companyId: string;
  companyName: string | undefined;
}) {
  // Ordena por prioridade: quem está na hora de voltar primeiro (mais atrasado
  // no topo), depois os próximos do vencimento, por fim os sem cadência.
  const sorted = useMemo(() => {
    const rank = (client: ClientResponse) => {
      const status = computeReturnStatus(client.last_visit_at, client.return_interval_days);
      if (status.isDue) {
        return -1_000_000 + (status.daysUntilDue ?? 0); // mais atrasado = menor
      }
      if (status.hasSchedule) {
        return status.daysUntilDue ?? 0;
      }
      return 1_000_000; // sem cadência vai para o fim
    };
    return [...clients].sort((a, b) => rank(a) - rank(b));
  }, [clients]);

  const dueCount = useMemo(
    () =>
      clients.filter(
        (client) => computeReturnStatus(client.last_visit_at, client.return_interval_days).isDue,
      ).length,
    [clients],
  );

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        {dueCount > 0
          ? `${dueCount} cliente(s) na hora de voltar. Toque em "Chamar no WhatsApp" para enviar o convite.`
          : "Nenhum cliente na hora de voltar agora. Configure a cadência de cada um para receber avisos."}
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        {sorted.map((client) => (
          <ClientReturnCard
            key={client.id}
            client={client}
            companyId={companyId}
            companyName={companyName}
          />
        ))}
      </div>
    </div>
  );
}

type ClientsTab = "list" | "return";

export function ClientsPage() {
  const { companyId } = useParams<{ companyId: string }>();
  const id = companyId ?? "";
  const { data: clients, isLoading } = useClients(id);
  const { data: blueprint } = useBlueprint(id);
  const { data: company } = useCompany(id);
  const [tab, setTab] = useState<ClientsTab>("list");

  const hasClients = (clients?.length ?? 0) > 0;

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-8">
      <PageHeader title="Clientes" description="Cadastro e histórico de relacionamento.">
        <NewClientDialog companyId={id} />
      </PageHeader>

      <div className="mb-6 inline-flex rounded-lg border bg-card p-1 text-sm">
        <button
          type="button"
          onClick={() => setTab("list")}
          className={
            tab === "list"
              ? "rounded-md bg-accent px-3 py-1.5 font-medium text-accent-foreground"
              : "rounded-md px-3 py-1.5 text-muted-foreground"
          }
        >
          Lista
        </button>
        <button
          type="button"
          onClick={() => setTab("return")}
          className={
            tab === "return"
              ? "rounded-md bg-accent px-3 py-1.5 font-medium text-accent-foreground"
              : "rounded-md px-3 py-1.5 text-muted-foreground"
          }
        >
          Retorno (WhatsApp)
        </button>
      </div>

      {isLoading && <Skeleton className="h-64 w-full" />}

      {!isLoading && !hasClients && (
        <EmptyState
          icon={Users}
          title="Nenhum cliente cadastrado"
          description="Cadastre clientes para vincular vendas e acompanhar o histórico de cada um."
        />
      )}

      {hasClients && tab === "list" && (
        <Card>
          <CardContent className="p-0">
            {(clients ?? []).map((client) => (
              <ClientDetailDialog
                key={client.id}
                client={client}
                companyId={id}
                customFieldDefs={blueprint?.client_custom_fields ?? []}
              />
            ))}
          </CardContent>
        </Card>
      )}

      {hasClients && tab === "return" && (
        <ClientReturnView clients={clients ?? []} companyId={id} companyName={company?.name} />
      )}
    </div>
  );
}
