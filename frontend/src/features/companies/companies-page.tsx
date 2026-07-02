import { motion } from "framer-motion";
import { ArrowRight, Building2, Plus } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useMyCompanies } from "@/features/companies/use-companies";
import type { CompanyRole } from "@/lib/api-types";

const ROLE_LABELS: Record<CompanyRole, string> = {
  owner: "Proprietário",
  admin: "Administrador",
  manager: "Gerente",
  employee: "Funcionário",
  viewer: "Visualizador",
};

export function CompaniesPage() {
  const { data: companies, isLoading } = useMyCompanies();

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Minhas empresas</h1>
          <p className="text-sm text-muted-foreground">
            Escolha uma empresa para abrir o painel ou cadastre uma nova.
          </p>
        </div>
        <Button asChild>
          <Link to="/onboarding">
            <Plus /> Nova empresa
          </Link>
        </Button>
      </div>

      {isLoading && (
        <div className="space-y-3">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      )}

      {!isLoading && (companies?.length ?? 0) === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-4 py-12 text-center">
            <div className="flex size-12 items-center justify-center rounded-full bg-accent text-accent-foreground">
              <Building2 className="size-6" />
            </div>
            <div>
              <p className="font-medium">Você ainda não tem empresas cadastradas</p>
              <p className="text-sm text-muted-foreground">
                Cadastre sua primeira empresa e deixe a IA montar um painel sob medida para o seu
                segmento.
              </p>
            </div>
            <Button asChild>
              <Link to="/onboarding">
                <Plus /> Cadastrar empresa
              </Link>
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="space-y-3">
        {companies?.map(({ company, role }, index) => (
          <motion.div
            key={company.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: index * 0.05 }}
          >
            <Link to={`/c/${company.id}`} className="block">
              <Card className="transition-colors hover:border-ring/60">
                <CardContent className="flex items-center justify-between p-5">
                  <div className="flex items-center gap-4">
                    <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <Building2 className="size-5" />
                    </div>
                    <div>
                      <p className="font-medium">{company.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {company.segment} · {company.city}/{company.state}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant="secondary">{ROLE_LABELS[role]}</Badge>
                    <ArrowRight className="size-4 text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
