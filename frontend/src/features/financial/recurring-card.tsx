import { zodResolver } from "@hookform/resolvers/zod";
import { CalendarClock, Play, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { EmptyState } from "@/components/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
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
import { useCategories } from "@/features/financial/use-financial";
import {
  FREQUENCY_LABELS,
  useCreateRecurring,
  useDeleteRecurring,
  useRecurring,
  useRunRecurring,
} from "@/features/financial/use-recurring";
import { extractErrorMessage } from "@/lib/api";
import type { RecurrenceFrequency } from "@/lib/api-types";
import { parseCurrencyToCents } from "@/lib/money";
import { formatCents } from "@/lib/utils";

const recurringSchema = z.object({
  category_id: z.string().min(1, "Selecione uma categoria."),
  type: z.enum(["income", "expense"]),
  amount: z
    .string()
    .min(1, "Informe o valor.")
    .refine((value) => {
      const cents = parseCurrencyToCents(value);
      return cents !== null && cents > 0;
    }, "Valor inválido — use o formato 1.234,56."),
  description: z.string().min(1, "Descreva a recorrência."),
  frequency: z.enum(["weekly", "monthly", "yearly"]),
  start_date: z.string().min(1, "Informe a data de início."),
  notes: z.string().optional(),
});

type RecurringForm = z.infer<typeof recurringSchema>;

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("pt-BR");
}

export function RecurringCard({ companyId }: { companyId: string }) {
  const [open, setOpen] = useState(false);
  const recurring = useRecurring(companyId);
  const categories = useCategories(companyId);
  const createRecurring = useCreateRecurring(companyId);
  const deleteRecurring = useDeleteRecurring(companyId);
  const runRecurring = useRunRecurring(companyId);

  const form = useForm<RecurringForm>({
    resolver: zodResolver(recurringSchema),
    defaultValues: {
      type: "expense",
      frequency: "monthly",
      start_date: new Date().toISOString().slice(0, 10),
    },
  });

  const submit = form.handleSubmit(async (values) => {
    const cents = parseCurrencyToCents(values.amount);
    if (cents === null) return;
    try {
      await createRecurring.mutateAsync({
        category_id: values.category_id,
        type: values.type,
        amount_cents: cents,
        description: values.description,
        frequency: values.frequency,
        start_date: `${values.start_date}T00:00:00Z`,
        notes: values.notes ?? null,
      });
      toast.success("Recorrência criada.");
      setOpen(false);
      form.reset({
        type: "expense",
        frequency: "monthly",
        start_date: new Date().toISOString().slice(0, 10),
      });
    } catch (error) {
      toast.error(extractErrorMessage(error));
    }
  });

  const runNow = async () => {
    try {
      const result = await runRecurring.mutateAsync();
      toast.success(
        result.created > 0
          ? `${result.created} lançamento(s) gerado(s).`
          : "Nenhuma recorrência vencida no momento.",
      );
    } catch (error) {
      toast.error(extractErrorMessage(error));
    }
  };

  const remove = async (id: string) => {
    try {
      await deleteRecurring.mutateAsync(id);
      toast.success("Recorrência removida.");
    } catch (error) {
      toast.error(extractErrorMessage(error));
    }
  };

  const items = recurring.data ?? [];

  return (
    <Card>
      <CardContent className="space-y-4 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="font-semibold">Lançamentos recorrentes</h3>
            <p className="text-sm text-muted-foreground">
              Aluguel, salários, assinaturas — gerados automaticamente a cada período.
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={runNow}
              disabled={runRecurring.isPending || items.length === 0}
            >
              <Play className="mr-1.5 size-4" />
              Gerar agora
            </Button>
            <Dialog open={open} onOpenChange={setOpen}>
              <DialogTrigger asChild>
                <Button size="sm">
                  <Plus className="mr-1.5 size-4" />
                  Nova recorrência
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Nova recorrência</DialogTitle>
                </DialogHeader>
                <form onSubmit={submit} className="space-y-4">
                  <div className="space-y-1.5">
                    <Label>Categoria</Label>
                    <Controller
                      control={form.control}
                      name="category_id"
                      render={({ field }) => (
                        <Select value={field.value} onValueChange={field.onChange}>
                          <SelectTrigger>
                            <SelectValue placeholder="Selecione" />
                          </SelectTrigger>
                          <SelectContent>
                            {(categories.data ?? []).map((category) => (
                              <SelectItem key={category.id} value={category.id}>
                                {category.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    />
                    {form.formState.errors.category_id && (
                      <p className="text-sm text-destructive">
                        {form.formState.errors.category_id.message}
                      </p>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label>Tipo</Label>
                      <Controller
                        control={form.control}
                        name="type"
                        render={({ field }) => (
                          <Select value={field.value} onValueChange={field.onChange}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="expense">Despesa</SelectItem>
                              <SelectItem value="income">Receita</SelectItem>
                            </SelectContent>
                          </Select>
                        )}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label>Periodicidade</Label>
                      <Controller
                        control={form.control}
                        name="frequency"
                        render={({ field }) => (
                          <Select value={field.value} onValueChange={field.onChange}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {(Object.keys(FREQUENCY_LABELS) as RecurrenceFrequency[]).map(
                                (frequency) => (
                                  <SelectItem key={frequency} value={frequency}>
                                    {FREQUENCY_LABELS[frequency]}
                                  </SelectItem>
                                ),
                              )}
                            </SelectContent>
                          </Select>
                        )}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label>Valor</Label>
                      <Input placeholder="1.234,56" {...form.register("amount")} />
                      {form.formState.errors.amount && (
                        <p className="text-sm text-destructive">
                          {form.formState.errors.amount.message}
                        </p>
                      )}
                    </div>
                    <div className="space-y-1.5">
                      <Label>Início / próximo vencimento</Label>
                      <Input type="date" {...form.register("start_date")} />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <Label>Descrição</Label>
                    <Input placeholder="Aluguel da loja" {...form.register("description")} />
                    {form.formState.errors.description && (
                      <p className="text-sm text-destructive">
                        {form.formState.errors.description.message}
                      </p>
                    )}
                  </div>

                  <DialogFooter>
                    <Button type="submit" disabled={createRecurring.isPending}>
                      Salvar
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {items.length === 0 ? (
          <EmptyState
            icon={CalendarClock}
            title="Nenhuma recorrência"
            description="Cadastre despesas e receitas fixas para que virem lançamentos sozinhas."
          />
        ) : (
          <ul className="divide-y">
            {items.map((item) => (
              <li key={item.id} className="flex items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <p className="truncate font-medium">{item.description}</p>
                  <p className="text-sm text-muted-foreground">
                    Próximo: {formatDate(item.next_run_date)}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span
                    className={item.type === "income" ? "text-emerald-600" : "text-destructive"}
                  >
                    {formatCents(item.amount_cents)}
                  </span>
                  <Badge variant="secondary">{FREQUENCY_LABELS[item.frequency]}</Badge>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => void remove(item.id)}
                    aria-label="Remover recorrência"
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
