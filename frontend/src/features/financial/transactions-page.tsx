import { zodResolver } from "@hookform/resolvers/zod";
import { Check, CircleDollarSign, Plus, Wallet, X } from "lucide-react";
import { useMemo, useState } from "react";
import { Controller, useForm } from "react-hook-form";
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
import { useSeedCategoriesFromBlueprint } from "@/features/blueprint/use-blueprint";
import { useClients } from "@/features/clients/use-clients";
import { ExportReportButton } from "@/features/reports/export-report-button";
import { AccountsSummaryCard } from "@/features/financial/accounts-summary-card";
import { RecurringCard } from "@/features/financial/recurring-card";
import {
  useCancelTransaction,
  useCategories,
  useCreateCategory,
  useCreateTransaction,
  useMarkTransactionPaid,
  useTransactions,
} from "@/features/financial/use-financial";
import { extractErrorMessage } from "@/lib/api";
import type {
  FinancialCategoryType,
  FinancialTransactionResponse,
  TransactionStatus,
} from "@/lib/api-types";
import { useCompanyCurrency } from "@/features/companies/use-company-currency";
import { parseCurrencyToCents } from "@/lib/money";
import { formatCents } from "@/lib/utils";

const STATUS_LABELS: Record<TransactionStatus, string> = {
  pending: "Pendente",
  paid: "Pago",
  cancelled: "Cancelado",
};

const transactionSchema = z.object({
  category_id: z.string().min(1, "Selecione uma categoria."),
  type: z.enum(["income", "expense"]),
  amount: z
    .string()
    .min(1, "Informe o valor.")
    .refine((value) => {
      const cents = parseCurrencyToCents(value);
      return cents !== null && cents > 0;
    }, "Valor inválido — use o formato 1.234,56."),
  description: z.string().min(1, "Descreva o lançamento.").max(500),
  when: z.enum(["paid", "pending"]),
  date: z.string().optional(),
  client_id: z.string().optional(),
  notes: z.string().max(2000).optional(),
});

type TransactionForm = z.infer<typeof transactionSchema>;

function NewTransactionDialog({ companyId }: { companyId: string }) {
  const [open, setOpen] = useState(false);
  const { data: categories } = useCategories(companyId);
  const { data: clients } = useClients(companyId);
  const createTransaction = useCreateTransaction(companyId);

  const {
    register,
    handleSubmit,
    control,
    watch,
    reset,
    formState: { errors },
  } = useForm<TransactionForm>({
    resolver: zodResolver(transactionSchema),
    defaultValues: { type: "income", when: "paid", category_id: "", client_id: "" },
  });

  const selectedType = watch("type");
  const filteredCategories = useMemo(
    () => (categories ?? []).filter((c) => c.type === selectedType && c.is_active),
    [categories, selectedType],
  );

  const onSubmit = handleSubmit((values) => {
    const cents = parseCurrencyToCents(values.amount);
    if (cents === null) {
      return;
    }
    const date = values.date ? new Date(values.date).toISOString() : new Date().toISOString();
    createTransaction.mutate(
      {
        category_id: values.category_id,
        type: values.type,
        amount_cents: cents,
        description: values.description,
        paid_at: values.when === "paid" ? date : null,
        due_date: values.when === "pending" ? date : null,
        client_id: values.client_id || null,
        notes: values.notes || null,
      },
      {
        onSuccess: () => {
          toast.success("Lançamento registrado!");
          reset();
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
          <Plus /> Novo lançamento
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Novo lançamento</DialogTitle>
          <DialogDescription>
            Receita ou despesa — pago agora ou com vencimento futuro.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Tipo</Label>
              <Controller
                control={control}
                name="type"
                render={({ field }) => (
                  <Select
                    value={field.value}
                    onValueChange={(value) => field.onChange(value as FinancialCategoryType)}
                  >
                    <SelectTrigger aria-label="Tipo">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="income">Receita</SelectItem>
                      <SelectItem value="expense">Despesa</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
            <div className="space-y-2">
              <Label>Categoria</Label>
              <Controller
                control={control}
                name="category_id"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger aria-label="Categoria">
                      <SelectValue placeholder="Selecione" />
                    </SelectTrigger>
                    <SelectContent>
                      {filteredCategories.map((category) => (
                        <SelectItem key={category.id} value={category.id}>
                          {category.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
              {errors.category_id && (
                <p role="alert" className="text-sm text-destructive">
                  {errors.category_id.message}
                </p>
              )}
              {filteredCategories.length === 0 && (
                <p className="text-xs text-muted-foreground">
                  Nenhuma categoria de {selectedType === "income" ? "receita" : "despesa"} — crie
                  uma em “Categorias”.
                </p>
              )}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="amount">Valor (R$)</Label>
              <Input
                id="amount"
                inputMode="decimal"
                placeholder="1.234,56"
                {...register("amount")}
              />
              {errors.amount && (
                <p role="alert" className="text-sm text-destructive">
                  {errors.amount.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label>Situação</Label>
              <Controller
                control={control}
                name="when"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger aria-label="Situação">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="paid">Já pago/recebido</SelectItem>
                      <SelectItem value="pending">Pendente (a pagar/receber)</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="date">
                {watch("when") === "paid" ? "Data do pagamento" : "Vencimento"}
              </Label>
              <Input id="date" type="date" {...register("date")} />
              <p className="text-xs text-muted-foreground">Vazio = hoje.</p>
            </div>
            {(clients?.length ?? 0) > 0 && (
              <div className="space-y-2">
                <Label>Cliente (opcional)</Label>
                <Controller
                  control={control}
                  name="client_id"
                  render={({ field }) => (
                    <Select value={field.value ?? ""} onValueChange={field.onChange}>
                      <SelectTrigger aria-label="Cliente">
                        <SelectValue placeholder="Nenhum" />
                      </SelectTrigger>
                      <SelectContent>
                        {(clients ?? []).map((client) => (
                          <SelectItem key={client.id} value={client.id}>
                            {client.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Descrição</Label>
            <Input id="description" placeholder="Ex.: Corte + barba" {...register("description")} />
            {errors.description && (
              <p role="alert" className="text-sm text-destructive">
                {errors.description.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Observações (opcional)</Label>
            <Textarea id="notes" {...register("notes")} />
          </div>

          <DialogFooter>
            <Button type="submit" disabled={createTransaction.isPending}>
              {createTransaction.isPending ? "Salvando…" : "Registrar lançamento"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

const categorySchema = z.object({
  name: z.string().min(1, "Informe o nome.").max(200),
  type: z.enum(["income", "expense"]),
});

type CategoryForm = z.infer<typeof categorySchema>;

function CategoriesDialog({ companyId }: { companyId: string }) {
  const { data: categories } = useCategories(companyId);
  const createCategory = useCreateCategory(companyId);
  const seedFromBlueprint = useSeedCategoriesFromBlueprint(companyId);

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<CategoryForm>({
    resolver: zodResolver(categorySchema),
    defaultValues: { type: "income" },
  });

  const onSubmit = handleSubmit((values) => {
    createCategory.mutate(values, {
      onSuccess: () => {
        toast.success("Categoria criada!");
        reset({ type: values.type, name: "" });
      },
      onError: (error) => toast.error(extractErrorMessage(error)),
    });
  });

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">Categorias</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Categorias financeiras</DialogTitle>
          <DialogDescription>
            Organize receitas e despesas. Você pode importar as sugestões da IA.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-wrap gap-2">
          {(categories ?? []).map((category) => (
            <Badge
              key={category.id}
              variant={category.type === "income" ? "success" : "destructive"}
            >
              {category.name}
            </Badge>
          ))}
          {(categories?.length ?? 0) === 0 && (
            <p className="text-sm text-muted-foreground">Nenhuma categoria ainda.</p>
          )}
        </div>

        <Button
          variant="secondary"
          size="sm"
          disabled={seedFromBlueprint.isPending}
          onClick={() =>
            seedFromBlueprint.mutate(undefined, {
              onSuccess: () => toast.success("Sugestões do blueprint importadas!"),
              onError: (error) => toast.error(extractErrorMessage(error)),
            })
          }
        >
          Importar sugestões da IA
        </Button>

        <form onSubmit={onSubmit} className="flex items-end gap-2" noValidate>
          <div className="flex-1 space-y-2">
            <Label htmlFor="category-name">Nova categoria</Label>
            <Input id="category-name" placeholder="Ex.: Vendas online" {...register("name")} />
            {errors.name && (
              <p role="alert" className="text-sm text-destructive">
                {errors.name.message}
              </p>
            )}
          </div>
          <Controller
            control={control}
            name="type"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger className="w-32" aria-label="Tipo da categoria">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="income">Receita</SelectItem>
                  <SelectItem value="expense">Despesa</SelectItem>
                </SelectContent>
              </Select>
            )}
          />
          <Button type="submit" disabled={createCategory.isPending}>
            Criar
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function TransactionRow({
  transaction,
  categoryName,
  companyId,
  currency,
}: {
  transaction: FinancialTransactionResponse;
  categoryName: string;
  companyId: string;
  currency: string;
}) {
  const markPaid = useMarkTransactionPaid(companyId);
  const cancel = useCancelTransaction(companyId);
  const isIncome = transaction.type === "income";

  return (
    <div className="flex items-center justify-between gap-3 border-b px-5 py-3 last:border-b-0">
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{transaction.description}</p>
        <p className="text-xs text-muted-foreground">
          {categoryName}
          {transaction.due_date &&
            transaction.status === "pending" &&
            ` · vence ${new Date(transaction.due_date).toLocaleDateString("pt-BR")}`}
          {transaction.paid_at && ` · ${new Date(transaction.paid_at).toLocaleDateString("pt-BR")}`}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-3">
        <Badge
          variant={
            transaction.status === "paid"
              ? "success"
              : transaction.status === "cancelled"
                ? "muted"
                : "secondary"
          }
        >
          {STATUS_LABELS[transaction.status]}
        </Badge>
        <span
          className={
            "text-sm font-semibold " +
            (transaction.status === "cancelled"
              ? "text-muted-foreground line-through"
              : isIncome
                ? "text-success"
                : "text-destructive")
          }
        >
          {isIncome ? "+" : "-"}
          {formatCents(transaction.amount_cents, currency)}
        </span>
        {transaction.status === "pending" && (
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="icon"
              aria-label="Marcar como pago"
              title="Marcar como pago"
              disabled={markPaid.isPending}
              onClick={() =>
                markPaid.mutate(transaction.id, {
                  onSuccess: () => toast.success("Lançamento marcado como pago!"),
                  onError: (error) => toast.error(extractErrorMessage(error)),
                })
              }
            >
              <Check className="text-success" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Cancelar lançamento"
              title="Cancelar lançamento"
              disabled={cancel.isPending}
              onClick={() =>
                cancel.mutate(transaction.id, {
                  onSuccess: () => toast.success("Lançamento cancelado."),
                  onError: (error) => toast.error(extractErrorMessage(error)),
                })
              }
            >
              <X className="text-destructive" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

export function TransactionsPage() {
  const { companyId } = useParams<{ companyId: string }>();
  const id = companyId ?? "";
  const currency = useCompanyCurrency(id);
  const [typeFilter, setTypeFilter] = useState<"all" | FinancialCategoryType>("all");
  const [statusFilter, setStatusFilter] = useState<"all" | TransactionStatus>("all");

  const filters = {
    ...(typeFilter !== "all" ? { type: typeFilter } : {}),
    ...(statusFilter !== "all" ? { status: statusFilter } : {}),
  };
  const { data: transactions, isLoading } = useTransactions(id, filters);
  const { data: categories } = useCategories(id);
  const categoryNames = useMemo(
    () => new Map((categories ?? []).map((c) => [c.id, c.name])),
    [categories],
  );

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-8">
      <PageHeader title="Financeiro" description="Receitas, despesas, contas a pagar e a receber.">
        <ExportReportButton companyId={id} report="financial" />
        <ExportReportButton companyId={id} report="accounts" label="Contas (CSV)" />
        <CategoriesDialog companyId={id} />
        <NewTransactionDialog companyId={id} />
      </PageHeader>

      <AccountsSummaryCard companyId={id} />

      <div className="mb-4 flex flex-wrap gap-2">
        <Select value={typeFilter} onValueChange={(v) => setTypeFilter(v as typeof typeFilter)}>
          <SelectTrigger className="w-36" aria-label="Filtrar por tipo">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os tipos</SelectItem>
            <SelectItem value="income">Receitas</SelectItem>
            <SelectItem value="expense">Despesas</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={statusFilter}
          onValueChange={(v) => setStatusFilter(v as typeof statusFilter)}
        >
          <SelectTrigger className="w-36" aria-label="Filtrar por situação">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas as situações</SelectItem>
            <SelectItem value="pending">Pendentes</SelectItem>
            <SelectItem value="paid">Pagos</SelectItem>
            <SelectItem value="cancelled">Cancelados</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading && <Skeleton className="h-64 w-full" />}

      {!isLoading && (transactions?.length ?? 0) === 0 && (
        <EmptyState
          icon={CircleDollarSign}
          title="Nenhum lançamento encontrado"
          description="Registre sua primeira receita ou despesa para começar a acompanhar o caixa."
        />
      )}

      {(transactions?.length ?? 0) > 0 && (
        <Card>
          <CardContent className="p-0">
            {(transactions ?? []).map((transaction) => (
              <TransactionRow
                key={transaction.id}
                transaction={transaction}
                categoryName={categoryNames.get(transaction.category_id) ?? "—"}
                companyId={id}
                currency={currency}
              />
            ))}
          </CardContent>
        </Card>
      )}

      <div className="mt-6">
        <RecurringCard companyId={id} />
      </div>

      <p className="mt-4 flex items-center gap-1.5 text-xs text-muted-foreground">
        <Wallet className="size-3.5" />
        Valores em centavos no backend — sem erros de arredondamento de ponto flutuante.
      </p>
    </div>
  );
}
