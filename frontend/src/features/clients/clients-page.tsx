import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, ShoppingBag, Users } from "lucide-react";
import { useState } from "react";
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
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useBlueprint } from "@/features/blueprint/use-blueprint";
import { useClientSummary, useClients, useCreateClient } from "@/features/clients/use-clients";
import { extractErrorMessage } from "@/lib/api";
import type { BlueprintCustomField, ClientResponse } from "@/lib/api-types";
import { formatCents } from "@/lib/utils";

const clientSchema = z.object({
  name: z.string().min(1, "Informe o nome do cliente.").max(200),
  email: z.string().email("E-mail inválido.").or(z.literal("")).optional(),
  phone: z.string().max(50).optional(),
  notes: z.string().max(2000).optional(),
  custom_fields: z.record(z.string()),
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
    createClient.mutate(
      {
        name: values.name,
        email: values.email || null,
        phone: values.phone || null,
        notes: values.notes || null,
        custom_fields: filledCustomFields,
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
              <Label htmlFor="client-phone">Telefone (opcional)</Label>
              <Input id="client-phone" {...register("phone")} />
            </div>
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
              {summary ? formatCents(summary.total_spent_cents) : "…"}
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

export function ClientsPage() {
  const { companyId } = useParams<{ companyId: string }>();
  const id = companyId ?? "";
  const { data: clients, isLoading } = useClients(id);
  const { data: blueprint } = useBlueprint(id);

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-8">
      <PageHeader title="Clientes" description="Cadastro e histórico de relacionamento.">
        <NewClientDialog companyId={id} />
      </PageHeader>

      {isLoading && <Skeleton className="h-64 w-full" />}

      {!isLoading && (clients?.length ?? 0) === 0 && (
        <EmptyState
          icon={Users}
          title="Nenhum cliente cadastrado"
          description="Cadastre clientes para vincular vendas e acompanhar o histórico de cada um."
        />
      )}

      {(clients?.length ?? 0) > 0 && (
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
    </div>
  );
}
