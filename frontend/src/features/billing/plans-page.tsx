import { AlertTriangle, Check, Crown, ExternalLink, Sparkles } from "lucide-react";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { toast } from "sonner";

import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useCancelSubscription,
  useChangePlan,
  usePlans,
  useStartCheckout,
  useSubscription,
} from "@/features/billing/use-plans";
import { extractErrorMessage } from "@/lib/api";
import type { BillingCycle, PlanResponse, PlanTier } from "@/lib/api-types";
import { cn, formatCents } from "@/lib/utils";

const TIER_ORDER: Record<PlanTier, number> = {
  starter: 0,
  professional: 1,
  business: 2,
  enterprise: 3,
};

const STATUS_LABEL: Record<string, string> = {
  trialing: "Em teste",
  active: "Ativo",
  past_due: "Pagamento pendente",
  canceled: "Cancelado",
};

// Enterprise é negociado, não contratado por botão. Sem endereço configurado,
// o botão some em vez de abrir um e-mail para lugar nenhum.
const SALES_EMAIL = import.meta.env.VITE_SALES_EMAIL as string | undefined;

function priceLabel(plan: PlanResponse, cycle: BillingCycle): string {
  if (plan.is_contact_sales) {
    return "Sob consulta";
  }
  const cents = cycle === "yearly" ? plan.price_cents_yearly : plan.price_cents_monthly;
  if (cents === 0) {
    return "Grátis";
  }
  const perYear = cycle === "yearly";
  const monthly = perYear ? Math.round(cents / 12) : cents;
  return `${formatCents(monthly)}/mês`;
}

function limitLabel(value: number): string {
  return value === -1 ? "Ilimitado" : String(value);
}

export function PlansPage() {
  const { companyId = "" } = useParams();
  const plansQuery = usePlans();
  const subscriptionQuery = useSubscription(companyId);
  const changePlan = useChangePlan(companyId);
  const startCheckout = useStartCheckout(companyId);
  const cancelSubscription = useCancelSubscription(companyId);
  const [cycle, setCycle] = useState<BillingCycle>("monthly");

  const current = subscriptionQuery.data;
  const currentTier = current?.tier ?? "starter";
  const isPending = changePlan.isPending || startCheckout.isPending;

  // Contratar não é trocar de plano: a chamada cria a cobrança e devolve a
  // página de pagamento. O plano só é liberado quando o dinheiro entra.
  const handleCheckout = (tier: PlanTier) => {
    startCheckout.mutate(
      { tier, billing_cycle: cycle },
      {
        onSuccess: (data) => window.location.assign(data.payment_url),
        onError: (error) => toast.error(extractErrorMessage(error)),
      },
    );
  };

  const handleTrial = (tier: PlanTier) => {
    changePlan.mutate(
      { tier, billing_cycle: cycle, start_trial: true },
      {
        onSuccess: (data) => {
          const name = plansQuery.data?.find((p) => p.tier === data.tier)?.name ?? data.tier;
          toast.success(`Teste do plano ${name} iniciado! Aproveite os 14 dias.`);
        },
        onError: (error) => toast.error(extractErrorMessage(error)),
      },
    );
  };

  const handleDowngradeToStarter = () => {
    changePlan.mutate(
      { tier: "starter", billing_cycle: cycle },
      {
        onSuccess: () => toast.success("Você voltou ao plano Starter."),
        onError: (error) => toast.error(extractErrorMessage(error)),
      },
    );
  };

  const handleCancel = () => {
    cancelSubscription.mutate(undefined, {
      onSuccess: () =>
        toast.success("Assinatura cancelada. A cobrança foi encerrada e você voltou ao Starter."),
      onError: (error) => toast.error(extractErrorMessage(error)),
    });
  };

  return (
    <div>
      <PageHeader
        title="Planos e assinatura"
        description="Escolha o plano ideal para o momento do seu negócio. Faça upgrade a qualquer momento."
      />

      {current?.payment_pending && current.pending_tier && (
        <PendingPaymentNotice
          planName={
            plansQuery.data?.find((p) => p.tier === current.pending_tier)?.name ??
            current.pending_tier
          }
          isPending={isPending}
          onResume={() => handleCheckout(current.pending_tier as PlanTier)}
        />
      )}

      {current && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex flex-wrap items-center gap-2 text-base">
              <Crown className="size-4 text-primary" />
              Seu plano atual:{" "}
              {plansQuery.data?.find((p) => p.tier === currentTier)?.name ?? currentTier}
              <Badge variant={current.status === "canceled" ? "warning" : "success"}>
                {STATUS_LABEL[current.status] ?? current.status}
              </Badge>
            </CardTitle>
            <CardDescription>
              {current.status === "trialing" && current.trial_ends_at
                ? `Seu teste termina em ${new Date(current.trial_ends_at).toLocaleDateString("pt-BR")}.`
                : current.current_period_end
                  ? `Período atual até ${new Date(current.current_period_end).toLocaleDateString("pt-BR")}.`
                  : "Plano gratuito, sem cobrança."}
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <UsageBar
              label="Usuários"
              current={current.usage.members}
              limit={current.limits.max_members}
            />
            <UsageBar
              label="Integrações"
              current={current.usage.integrations}
              limit={current.limits.max_integrations}
            />
          </CardContent>
        </Card>
      )}

      <div className="mb-2 flex items-center justify-center gap-2">
        <CycleToggle cycle={cycle} onChange={setCycle} />
      </div>
      <p className="mb-6 text-center text-xs text-muted-foreground">
        Pagamento por Pix, boleto ou cartão. Cancele quando quiser.
      </p>

      {plansQuery.isLoading ? (
        <div className="grid gap-4 lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-96" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-4">
          {plansQuery.data?.map((plan) => (
            <PlanCard
              key={plan.tier}
              plan={plan}
              cycle={cycle}
              currentTier={currentTier}
              trialUsed={current?.trial_used ?? false}
              isPending={isPending}
              onCheckout={handleCheckout}
              onTrial={handleTrial}
              onDowngradeToStarter={handleDowngradeToStarter}
            />
          ))}
        </div>
      )}

      {current && currentTier !== "starter" && current.status !== "canceled" && (
        <div className="mt-6 text-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCancel}
            disabled={cancelSubscription.isPending}
            className="text-muted-foreground"
          >
            {cancelSubscription.isPending ? "Cancelando…" : "Cancelar assinatura"}
          </Button>
        </div>
      )}
    </div>
  );
}

function CycleToggle({
  cycle,
  onChange,
}: {
  cycle: BillingCycle;
  onChange: (cycle: BillingCycle) => void;
}) {
  return (
    <div className="inline-flex rounded-lg border bg-muted/40 p-1 text-sm">
      <button
        type="button"
        onClick={() => onChange("monthly")}
        className={cn(
          "rounded-md px-4 py-1.5 font-medium transition-colors",
          cycle === "monthly" ? "bg-background shadow-sm" : "text-muted-foreground",
        )}
      >
        Mensal
      </button>
      <button
        type="button"
        onClick={() => onChange("yearly")}
        className={cn(
          "flex items-center gap-1.5 rounded-md px-4 py-1.5 font-medium transition-colors",
          cycle === "yearly" ? "bg-background shadow-sm" : "text-muted-foreground",
        )}
      >
        Anual
        <Badge variant="success" className="text-[10px]">
          -17%
        </Badge>
      </button>
    </div>
  );
}

function UsageBar({ label, current, limit }: { label: string; current: number; limit: number }) {
  const unlimited = limit === -1;
  const pct = unlimited ? 0 : Math.min(100, Math.round((current / Math.max(limit, 1)) * 100));
  const nearLimit = !unlimited && pct >= 80;
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">
          {current} / {unlimited ? "∞" : limit}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div
          className={cn(
            "h-full rounded-full transition-all",
            nearLimit ? "bg-warning" : "bg-primary",
          )}
          style={{ width: unlimited ? "8%" : `${pct}%` }}
        />
      </div>
    </div>
  );
}

function PendingPaymentNotice({
  planName,
  isPending,
  onResume,
}: {
  planName: string;
  isPending: boolean;
  onResume: () => void;
}) {
  return (
    <Card className="mb-6 border-warning bg-warning/5">
      <CardContent className="flex flex-wrap items-center gap-3 py-4">
        <AlertTriangle className="size-5 shrink-0 text-warning" />
        <div className="flex-1 text-sm">
          <p className="font-medium">Pagamento pendente do plano {planName}</p>
          <p className="text-muted-foreground">
            A contratação foi criada, mas o pagamento ainda não foi confirmado. O plano é liberado
            assim que ele cair.
          </p>
        </div>
        <Button size="sm" onClick={onResume} disabled={isPending}>
          {isPending ? "Abrindo…" : "Concluir pagamento"}
        </Button>
      </CardContent>
    </Card>
  );
}

function PlanCard({
  plan,
  cycle,
  currentTier,
  trialUsed,
  isPending,
  onCheckout,
  onTrial,
  onDowngradeToStarter,
}: {
  plan: PlanResponse;
  cycle: BillingCycle;
  currentTier: PlanTier;
  trialUsed: boolean;
  isPending: boolean;
  onCheckout: (tier: PlanTier) => void;
  onTrial: (tier: PlanTier) => void;
  onDowngradeToStarter: () => void;
}) {
  const isCurrent = plan.tier === currentTier;
  const isUpgrade = TIER_ORDER[plan.tier] > TIER_ORDER[currentTier];
  const isPaid = plan.price_cents_monthly > 0;
  // O teste é uma vez por empresa: oferecer de novo a quem já usou só produz
  // um erro depois do clique.
  const canTrial = isPaid && !plan.is_contact_sales && currentTier === "starter" && !trialUsed;

  return (
    <Card
      className={cn(
        "relative flex flex-col",
        plan.badge && "border-primary shadow-md",
        isCurrent && "ring-2 ring-primary",
      )}
    >
      {plan.badge && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <Badge className="gap-1">
            <Sparkles className="size-3" /> {plan.badge}
          </Badge>
        </div>
      )}
      <CardHeader>
        <CardTitle className="text-lg">{plan.name}</CardTitle>
        <CardDescription>{plan.tagline}</CardDescription>
        <div className="pt-2">
          <span className="text-2xl font-bold tracking-tight">{priceLabel(plan, cycle)}</span>
        </div>
        <p className="text-xs text-muted-foreground">{plan.target_audience}</p>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col">
        <ul className="mb-6 flex-1 space-y-2 text-sm">
          {plan.highlights.map((highlight) => (
            <li key={highlight} className="flex items-start gap-2">
              <Check className="mt-0.5 size-4 shrink-0 text-success" />
              <span>{highlight}</span>
            </li>
          ))}
        </ul>
        <div className="space-y-2 border-t pt-3 text-xs text-muted-foreground">
          <div className="flex justify-between">
            <span>Usuários</span>
            <span className="font-medium text-foreground">
              {limitLabel(plan.limits.max_members)}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Integrações</span>
            <span className="font-medium text-foreground">
              {limitLabel(plan.limits.max_integrations)}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Insights de IA / mês</span>
            <span className="font-medium text-foreground">
              {limitLabel(plan.limits.max_ai_insights_per_month)}
            </span>
          </div>
        </div>
        <div className="mt-4 space-y-2">
          {isCurrent ? (
            <Button variant="outline" disabled className="w-full">
              Plano atual
            </Button>
          ) : plan.is_contact_sales ? (
            // Enterprise é negociado. Antes este botão trocava o plano e dava
            // acesso ilimitado a quem clicasse em "Falar com vendas".
            SALES_EMAIL ? (
              <Button asChild variant={isUpgrade ? "default" : "outline"} className="w-full">
                <a href={`mailto:${SALES_EMAIL}?subject=Plano ${plan.name}`}>
                  Falar com vendas
                  <ExternalLink className="size-4" />
                </a>
              </Button>
            ) : null
          ) : !isPaid ? (
            <Button
              variant="outline"
              className="w-full"
              disabled={isPending}
              onClick={onDowngradeToStarter}
            >
              Voltar ao gratuito
            </Button>
          ) : (
            <>
              <Button
                variant={isUpgrade ? "default" : "outline"}
                className="w-full"
                disabled={isPending}
                onClick={() => onCheckout(plan.tier)}
              >
                {isPending ? "Abrindo pagamento…" : "Assinar"}
              </Button>
              {canTrial && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full text-primary"
                  disabled={isPending}
                  onClick={() => onTrial(plan.tier)}
                >
                  Testar 14 dias grátis
                </Button>
              )}
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
