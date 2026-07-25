import { Check, Crown, Sparkles } from "lucide-react";
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
  const cancelSubscription = useCancelSubscription(companyId);
  const [cycle, setCycle] = useState<BillingCycle>("monthly");

  const current = subscriptionQuery.data;
  const currentTier = current?.tier ?? "starter";

  const handleSelect = (tier: PlanTier, startTrial: boolean) => {
    changePlan.mutate(
      { tier, billing_cycle: cycle, start_trial: startTrial },
      {
        onSuccess: (data) => {
          const name = plansQuery.data?.find((p) => p.tier === data.tier)?.name ?? data.tier;
          toast.success(
            data.status === "trialing"
              ? `Teste do plano ${name} iniciado! Aproveite os 14 dias.`
              : `Plano alterado para ${name}.`,
          );
        },
        onError: (error) => toast.error(extractErrorMessage(error)),
      },
    );
  };

  const handleCancel = () => {
    cancelSubscription.mutate(undefined, {
      onSuccess: () => toast.success("Assinatura cancelada. Você voltou ao plano Starter."),
      onError: (error) => toast.error(extractErrorMessage(error)),
    });
  };

  return (
    <div>
      <PageHeader
        title="Planos e assinatura"
        description="Escolha o plano ideal para o momento do seu negócio. Faça upgrade a qualquer momento."
      />

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

      <div className="mb-6 flex items-center justify-center gap-2">
        <CycleToggle cycle={cycle} onChange={setCycle} />
      </div>

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
              isPending={changePlan.isPending}
              onSelect={handleSelect}
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

function PlanCard({
  plan,
  cycle,
  currentTier,
  isPending,
  onSelect,
}: {
  plan: PlanResponse;
  cycle: BillingCycle;
  currentTier: PlanTier;
  isPending: boolean;
  onSelect: (tier: PlanTier, startTrial: boolean) => void;
}) {
  const isCurrent = plan.tier === currentTier;
  const isUpgrade = TIER_ORDER[plan.tier] > TIER_ORDER[currentTier];
  const isDowngrade = TIER_ORDER[plan.tier] < TIER_ORDER[currentTier];
  const isPaid = plan.price_cents_monthly > 0;
  const canTrial = isPaid && !plan.is_contact_sales && currentTier === "starter";

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
            <Button
              variant={isUpgrade ? "default" : "outline"}
              className="w-full"
              disabled={isPending}
              onClick={() => onSelect(plan.tier, false)}
            >
              Falar com vendas
            </Button>
          ) : (
            <>
              <Button
                variant={isUpgrade ? "default" : "outline"}
                className="w-full"
                disabled={isPending}
                onClick={() => onSelect(plan.tier, false)}
              >
                {isDowngrade ? "Fazer downgrade" : isPaid ? "Assinar" : "Selecionar"}
              </Button>
              {canTrial && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full text-primary"
                  disabled={isPending}
                  onClick={() => onSelect(plan.tier, true)}
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
