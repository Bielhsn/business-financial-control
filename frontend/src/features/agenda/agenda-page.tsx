import { zodResolver } from "@hookform/resolvers/zod";
import { CalendarDays, ChevronLeft, ChevronRight, Clock, Plus, UserRound } from "lucide-react";
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
import {
  useAppointments,
  useChangeAppointmentStatus,
  useCreateAppointment,
} from "@/features/agenda/use-agenda";
import { useCatalogItems } from "@/features/catalog/use-catalog";
import { useClients } from "@/features/clients/use-clients";
import { useCompanyCurrency } from "@/features/companies/use-company-currency";
import { useEmployees } from "@/features/employees/use-employees";
import { extractErrorMessage } from "@/lib/api";
import type { AppointmentResponse, AppointmentStatus } from "@/lib/api-types";
import { parseCurrencyToCents } from "@/lib/money";
import { formatCents } from "@/lib/utils";

const NONE = "__none__";

/** Início/fim do dia (hora local) em ISO, para a janela de consulta. */
function dayBounds(day: Date): { start: string; end: string } {
  const start = new Date(day.getFullYear(), day.getMonth(), day.getDate(), 0, 0, 0);
  const end = new Date(day.getFullYear(), day.getMonth(), day.getDate() + 1, 0, 0, 0);
  return { start: start.toISOString(), end: end.toISOString() };
}

function toDateInputValue(day: Date): string {
  const offset = day.getTimezoneOffset();
  return new Date(day.getTime() - offset * 60000).toISOString().slice(0, 10);
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

const STATUS_META: Record<
  AppointmentStatus,
  { label: string; variant: "secondary" | "success" | "destructive" | "muted" }
> = {
  scheduled: { label: "Marcado", variant: "secondary" },
  completed: { label: "Concluído", variant: "success" },
  cancelled: { label: "Cancelado", variant: "muted" },
  no_show: { label: "Faltou", variant: "destructive" },
};

const appointmentSchema = z
  .object({
    service_id: z.string(),
    title: z.string().max(200).optional(),
    date: z.string().min(1, "Informe a data."),
    time: z.string().min(1, "Informe o horário."),
    duration: z.coerce
      .number({ invalid_type_error: "Informe a duração." })
      .int()
      .min(1, "Mínimo 1 minuto.")
      .max(24 * 60),
    client_id: z.string(),
    employee_id: z.string(),
    price: z.string().optional(),
    notes: z.string().max(2000).optional(),
  })
  .refine((data) => data.service_id !== NONE || (data.title?.trim().length ?? 0) > 0, {
    message: "Escolha um serviço ou informe um título.",
    path: ["title"],
  });

type AppointmentForm = z.infer<typeof appointmentSchema>;

function NewAppointmentDialog({ companyId, day }: { companyId: string; day: Date }) {
  const [open, setOpen] = useState(false);
  const createAppointment = useCreateAppointment(companyId);
  const { data: clients } = useClients(companyId);
  const { data: employees } = useEmployees(companyId);
  const { data: catalogItems } = useCatalogItems(companyId);
  const services = (catalogItems ?? []).filter((item) => item.kind === "service");

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<AppointmentForm>({
    resolver: zodResolver(appointmentSchema),
    defaultValues: {
      service_id: NONE,
      client_id: NONE,
      employee_id: NONE,
      date: toDateInputValue(day),
      time: "09:00",
      duration: 30,
    },
  });

  const onSubmit = handleSubmit((values) => {
    const startsAt = new Date(`${values.date}T${values.time}`);
    if (Number.isNaN(startsAt.getTime())) {
      toast.error("Data ou horário inválidos.");
      return;
    }
    const price = values.price ? parseCurrencyToCents(values.price) : null;
    if (values.price && price === null) {
      toast.error("Preço inválido — use o formato 1.234,56.");
      return;
    }
    createAppointment.mutate(
      {
        starts_at: startsAt.toISOString(),
        duration_minutes: values.duration,
        title: values.service_id === NONE ? values.title?.trim() || null : null,
        catalog_item_id: values.service_id === NONE ? null : values.service_id,
        client_id: values.client_id === NONE ? null : values.client_id,
        employee_id: values.employee_id === NONE ? null : values.employee_id,
        price_cents: price,
        notes: values.notes?.trim() || null,
      },
      {
        onSuccess: () => {
          toast.success("Agendamento criado!");
          reset({
            service_id: NONE,
            client_id: NONE,
            employee_id: NONE,
            date: values.date,
            time: values.time,
            duration: 30,
          });
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
          <Plus /> Novo agendamento
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[88vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Novo agendamento</DialogTitle>
          <DialogDescription>
            Selecione um serviço do catálogo (preço e nome vêm dele) ou digite um título livre.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          <div className="space-y-2">
            <Label>Serviço</Label>
            <Controller
              control={control}
              name="service_id"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger aria-label="Serviço">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={NONE}>Sem serviço (título livre)</SelectItem>
                    {services.map((service) => (
                      <SelectItem key={service.id} value={service.id}>
                        {service.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="appt-title">Título (se não escolher serviço)</Label>
            <Input id="appt-title" placeholder="Ex.: Corte masculino" {...register("title")} />
            {errors.title && (
              <p role="alert" className="text-sm text-destructive">
                {errors.title.message}
              </p>
            )}
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="appt-date">Data</Label>
              <Input id="appt-date" type="date" {...register("date")} />
              {errors.date && (
                <p role="alert" className="text-sm text-destructive">
                  {errors.date.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="appt-time">Horário</Label>
              <Input id="appt-time" type="time" {...register("time")} />
              {errors.time && (
                <p role="alert" className="text-sm text-destructive">
                  {errors.time.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="appt-duration">Duração (min)</Label>
              <Input id="appt-duration" type="number" min={1} {...register("duration")} />
              {errors.duration && (
                <p role="alert" className="text-sm text-destructive">
                  {errors.duration.message}
                </p>
              )}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Cliente</Label>
              <Controller
                control={control}
                name="client_id"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger aria-label="Cliente">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={NONE}>Sem cliente</SelectItem>
                      {(clients ?? []).map((c) => (
                        <SelectItem key={c.id} value={c.id}>
                          {c.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
            <div className="space-y-2">
              <Label>Profissional</Label>
              <Controller
                control={control}
                name="employee_id"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger aria-label="Profissional">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={NONE}>Sem profissional</SelectItem>
                      {(employees ?? []).map((e) => (
                        <SelectItem key={e.id} value={e.id}>
                          {e.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="appt-price">Preço (R$, opcional)</Label>
              <Input
                id="appt-price"
                inputMode="decimal"
                placeholder="Herda do serviço"
                {...register("price")}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="appt-notes">Observações</Label>
              <Input id="appt-notes" {...register("notes")} />
            </div>
          </div>

          <DialogFooter>
            <Button type="submit" disabled={createAppointment.isPending}>
              {createAppointment.isPending ? "Salvando…" : "Agendar"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function AppointmentCard({
  appointment,
  companyId,
  currency,
}: {
  appointment: AppointmentResponse;
  companyId: string;
  currency: string;
}) {
  const changeStatus = useChangeAppointmentStatus(companyId);
  const meta = STATUS_META[appointment.status];

  const setStatus = (status: AppointmentStatus) =>
    changeStatus.mutate(
      { id: appointment.id, status },
      {
        onSuccess: () => {
          if (status === "completed" && appointment.price_cents) {
            toast.success("Concluído! Receita lançada no financeiro.");
          } else {
            toast.success("Status atualizado.");
          }
        },
        onError: (error) => toast.error(extractErrorMessage(error)),
      },
    );

  return (
    <Card>
      <CardContent className="flex flex-wrap items-center justify-between gap-3 p-4">
        <div className="flex items-start gap-3">
          <div className="flex flex-col items-center rounded-md bg-accent px-2 py-1 text-accent-foreground">
            <Clock className="size-3.5" />
            <span className="text-sm font-semibold">{formatTime(appointment.starts_at)}</span>
          </div>
          <div className="min-w-0">
            <p className="font-medium">{appointment.title}</p>
            <p className="text-xs text-muted-foreground">
              {[
                `${appointment.duration_minutes} min`,
                appointment.client_name,
                appointment.employee_name && `com ${appointment.employee_name}`,
                appointment.price_cents != null && formatCents(appointment.price_cents, currency),
              ]
                .filter(Boolean)
                .join(" · ")}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={meta.variant}>{meta.label}</Badge>
          {appointment.status === "scheduled" && (
            <div className="flex gap-1">
              <Button
                size="sm"
                variant="secondary"
                disabled={changeStatus.isPending}
                onClick={() => setStatus("completed")}
              >
                Concluir
              </Button>
              <Button
                size="sm"
                variant="ghost"
                disabled={changeStatus.isPending}
                onClick={() => setStatus("no_show")}
              >
                Faltou
              </Button>
              <Button
                size="sm"
                variant="ghost"
                disabled={changeStatus.isPending}
                onClick={() => setStatus("cancelled")}
              >
                Cancelar
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function AgendaPage() {
  const { companyId } = useParams<{ companyId: string }>();
  const id = companyId ?? "";
  const [day, setDay] = useState(() => new Date());
  const currency = useCompanyCurrency(id);
  const { start, end } = useMemo(() => dayBounds(day), [day]);
  const { data: appointments, isLoading } = useAppointments(id, start, end);

  const shiftDay = (delta: number) =>
    setDay((current) => {
      const next = new Date(current);
      next.setDate(next.getDate() + delta);
      return next;
    });

  const isToday = toDateInputValue(day) === toDateInputValue(new Date());
  const sorted = (appointments ?? [])
    .slice()
    .sort((a, b) => a.starts_at.localeCompare(b.starts_at));

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8">
      <PageHeader
        title="Agenda"
        description="Agendamentos do dia. Ao concluir com preço, a receita entra no financeiro."
      >
        <NewAppointmentDialog companyId={id} day={day} />
      </PageHeader>

      <div className="mb-6 flex items-center justify-between gap-2 rounded-lg border bg-card p-2">
        <Button variant="ghost" size="icon" aria-label="Dia anterior" onClick={() => shiftDay(-1)}>
          <ChevronLeft />
        </Button>
        <div className="flex flex-col items-center">
          <span className="text-sm font-medium capitalize">
            {day.toLocaleDateString("pt-BR", {
              weekday: "long",
              day: "2-digit",
              month: "long",
            })}
          </span>
          {!isToday && (
            <button
              type="button"
              onClick={() => setDay(new Date())}
              className="text-xs text-primary hover:underline"
            >
              Voltar para hoje
            </button>
          )}
        </div>
        <Button variant="ghost" size="icon" aria-label="Próximo dia" onClick={() => shiftDay(1)}>
          <ChevronRight />
        </Button>
      </div>

      {isLoading && <Skeleton className="h-40 w-full" />}

      {!isLoading && sorted.length === 0 && (
        <EmptyState
          icon={CalendarDays}
          title="Nenhum agendamento neste dia"
          description="Crie um novo agendamento — você pode vincular cliente, profissional e serviço."
        />
      )}

      {sorted.length > 0 && (
        <div className="space-y-3">
          {sorted.map((appointment) => (
            <AppointmentCard
              key={appointment.id}
              appointment={appointment}
              companyId={id}
              currency={currency}
            />
          ))}
        </div>
      )}

      <p className="mt-6 flex items-center gap-1.5 text-xs text-muted-foreground">
        <UserRound className="size-3.5" /> Dica: cadastre seus profissionais em Funcionários para
        organizar a agenda por pessoa.
      </p>
    </div>
  );
}
