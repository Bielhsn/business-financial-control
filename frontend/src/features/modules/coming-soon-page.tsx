import { motion } from "framer-motion";
import {
  ArrowRight,
  FileText,
  FolderKanban,
  Hammer,
  Repeat,
  Sparkles,
  type LucideIcon,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface ComingSoonPageProps {
  icon: LucideIcon;
  title: string;
  description: string;
  /** Sugestão de como resolver hoje com os módulos existentes. */
  meanwhile: string;
  meanwhileRoute: string;
  meanwhileLabel: string;
}

export function ComingSoonPage({
  icon: Icon,
  title,
  description,
  meanwhile,
  meanwhileRoute,
  meanwhileLabel,
}: ComingSoonPageProps) {
  const { companyId } = useParams<{ companyId: string }>();

  return (
    <div className="mx-auto w-full max-w-2xl px-4 py-16">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Card>
          <CardContent className="flex flex-col items-center gap-4 py-12 text-center">
            <div className="flex size-14 items-center justify-center rounded-2xl bg-accent text-accent-foreground">
              <Icon className="size-7" />
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center justify-center gap-2">
                <h1 className="font-display text-2xl font-semibold tracking-tight">{title}</h1>
                <Badge variant="secondary" className="gap-1">
                  <Hammer className="size-3" /> Em desenvolvimento
                </Badge>
              </div>
              <p className="mx-auto max-w-md text-sm text-muted-foreground">{description}</p>
            </div>
            <div className="mt-2 w-full max-w-md rounded-lg border bg-background p-4 text-left">
              <p className="flex items-center gap-1.5 text-xs font-medium text-primary">
                <Sparkles className="size-3.5" /> Ativado pela IA para o seu segmento
              </p>
              <p className="mt-1.5 text-sm text-muted-foreground">{meanwhile}</p>
              <Button variant="secondary" size="sm" className="mt-3" asChild>
                <Link to={`/c/${companyId}/${meanwhileRoute}`}>
                  {meanwhileLabel} <ArrowRight />
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}

/* Páginas dos módulos ativáveis por segmento que ainda não têm backend próprio.
   Uma rota por módulo mantém URLs estáveis para quando a funcionalidade chegar. */

export function SubscriptionsPage() {
  return (
    <ComingSoonPage
      icon={Repeat}
      title="Assinaturas"
      description="Receita recorrente: planos, mensalidades, MRR, churn e cobranças automáticas."
      meanwhile="Enquanto isso, lance as mensalidades como receitas pendentes com vencimento — o fluxo de caixa e as contas a receber já organizam a recorrência."
      meanwhileRoute="transactions"
      meanwhileLabel="Lançar mensalidades"
    />
  );
}

export function ProjectsPage() {
  return (
    <ComingSoonPage
      icon={FolderKanban}
      title="Projetos"
      description="Gestão de projetos e custos por projeto, com margem e horas por cliente."
      meanwhile="Enquanto isso, crie uma categoria financeira por projeto — receitas e despesas por categoria já mostram a margem de cada um no dashboard."
      meanwhileRoute="transactions"
      meanwhileLabel="Organizar categorias"
    />
  );
}

export function ContractsPage() {
  return (
    <ComingSoonPage
      icon={FileText}
      title="Contratos"
      description="Contratos firmados com clientes: vigência, reajustes e renovações."
      meanwhile="Enquanto isso, use as observações do cadastro de clientes para registrar vigências e valores de contrato."
      meanwhileRoute="clients"
      meanwhileLabel="Abrir clientes"
    />
  );
}
