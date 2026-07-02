import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, UserRound } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useParams } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
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
import { useCreateEmployee, useEmployees } from "@/features/employees/use-employees";
import { extractErrorMessage } from "@/lib/api";

const employeeSchema = z.object({
  name: z.string().min(1, "Informe o nome.").max(200),
  email: z.string().email("E-mail inválido.").or(z.literal("")).optional(),
  phone: z.string().max(50).optional(),
  role_title: z.string().max(200).optional(),
});

type EmployeeForm = z.infer<typeof employeeSchema>;

function NewEmployeeDialog({ companyId }: { companyId: string }) {
  const [open, setOpen] = useState(false);
  const createEmployee = useCreateEmployee(companyId);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<EmployeeForm>({ resolver: zodResolver(employeeSchema) });

  const onSubmit = handleSubmit((values) => {
    createEmployee.mutate(
      {
        name: values.name,
        email: values.email || null,
        phone: values.phone || null,
        role_title: values.role_title || null,
      },
      {
        onSuccess: () => {
          toast.success("Funcionário cadastrado!");
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
          <Plus /> Novo funcionário
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Novo funcionário</DialogTitle>
          <DialogDescription>Cadastro simples de funcionários e prestadores.</DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          <div className="space-y-2">
            <Label htmlFor="employee-name">Nome</Label>
            <Input id="employee-name" {...register("name")} />
            {errors.name && (
              <p role="alert" className="text-sm text-destructive">
                {errors.name.message}
              </p>
            )}
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="employee-email">E-mail (opcional)</Label>
              <Input id="employee-email" type="email" {...register("email")} />
              {errors.email && (
                <p role="alert" className="text-sm text-destructive">
                  {errors.email.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="employee-phone">Telefone (opcional)</Label>
              <Input id="employee-phone" {...register("phone")} />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="employee-role">Cargo/função (opcional)</Label>
            <Input
              id="employee-role"
              placeholder="Ex.: Barbeiro, Atendente…"
              {...register("role_title")}
            />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={createEmployee.isPending}>
              {createEmployee.isPending ? "Salvando…" : "Cadastrar"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export function EmployeesPage() {
  const { companyId } = useParams<{ companyId: string }>();
  const id = companyId ?? "";
  const { data: employees, isLoading } = useEmployees(id);

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-8">
      <PageHeader title="Funcionários" description="Equipe e prestadores da empresa.">
        <NewEmployeeDialog companyId={id} />
      </PageHeader>

      {isLoading && <Skeleton className="h-64 w-full" />}

      {!isLoading && (employees?.length ?? 0) === 0 && (
        <EmptyState
          icon={UserRound}
          title="Nenhum funcionário cadastrado"
          description="Cadastre sua equipe para organizar funções e, futuramente, comissões e agenda."
        />
      )}

      {(employees?.length ?? 0) > 0 && (
        <Card>
          <CardContent className="p-0">
            {(employees ?? []).map((employee) => (
              <div
                key={employee.id}
                className="flex items-center justify-between gap-3 border-b px-5 py-3 last:border-b-0"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                    {employee.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{employee.name}</p>
                    <p className="truncate text-xs text-muted-foreground">
                      {[employee.role_title, employee.email, employee.phone]
                        .filter(Boolean)
                        .join(" · ") || "Sem detalhes"}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
