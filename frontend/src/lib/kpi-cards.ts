import { TrendingDown, TrendingUp, Users, Wallet, type LucideIcon } from "lucide-react";

import type { DashboardSummaryResponse, SegmentProfileResponse } from "@/lib/api-types";
import { formatCents } from "@/lib/utils";

export interface KpiCard {
  key: string;
  title: string;
  value: string;
  icon: LucideIcon;
  change: number | null;
  tone: "positive" | "negative" | "neutral";
}

/** Conjunto exibido quando o segmento não elege indicadores próprios. */
const CLASSIC_METRICS = ["total_revenue", "total_expenses", "profit", "active_clients"];

const NUMBER_FORMAT = new Intl.NumberFormat("pt-BR");
const PERCENT_FORMAT = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 });

/**
 * Monta os cartões do dashboard a partir das métricas que o perfil do segmento
 * elege como relevantes — e com o vocabulário do negócio.
 *
 * Uma barbearia vê "Atendimentos" e "Ticket médio"; uma loja de bebidas vê
 * "Margem" e "Vendas"; uma clínica vê "Pacientes ativos". Antes, todo mundo via
 * os mesmos quatro cartões fixos (Receita/Despesas/Lucro/Clientes ativos).
 *
 * O backend já calcula todas as métricas — aqui é só seleção e rótulo.
 */
export function buildKpiCards(
  profile: SegmentProfileResponse,
  data: DashboardSummaryResponse,
  currency: string,
): KpiCard[] {
  const { terminology } = profile;

  const byMetric: Record<string, KpiCard> = {
    total_revenue: {
      key: "total_revenue",
      title: "Receita",
      value: formatCents(data.revenue_cents, currency),
      icon: TrendingUp,
      change: data.comparison.revenue_change_pct,
      tone: "positive",
    },
    total_expenses: {
      key: "total_expenses",
      title: "Despesas",
      value: formatCents(data.expense_cents, currency),
      icon: TrendingDown,
      change: data.comparison.expense_change_pct,
      tone: "negative",
    },
    profit: {
      key: "profit",
      title: "Lucro",
      value: formatCents(data.profit_cents, currency),
      icon: Wallet,
      change: data.comparison.profit_change_pct,
      tone: data.profit_cents >= 0 ? "positive" : "negative",
    },
    profit_margin: {
      key: "profit_margin",
      title: "Margem de lucro",
      value:
        data.profit_margin_pct === null ? "—" : `${PERCENT_FORMAT.format(data.profit_margin_pct)}%`,
      icon: Wallet,
      change: null,
      tone: (data.profit_margin_pct ?? 0) >= 0 ? "positive" : "negative",
    },
    average_ticket: {
      key: "average_ticket",
      title: "Ticket médio",
      value: formatCents(data.average_ticket_cents, currency),
      icon: TrendingUp,
      change: null,
      tone: "neutral",
    },
    transaction_count: {
      key: "transaction_count",
      // "Atendimentos" na barbearia, "Vendas" no varejo, "Pedidos" no delivery.
      title: terminology.transactions,
      value: NUMBER_FORMAT.format(data.transaction_count),
      icon: TrendingUp,
      change: null,
      tone: "neutral",
    },
    active_clients: {
      key: "active_clients",
      title: `${terminology.clients} ativos`,
      value: NUMBER_FORMAT.format(data.active_clients),
      icon: Users,
      change: null,
      tone: "neutral",
    },
  };

  // O type guard remove o undefined de métricas que o backend conheça e o
  // frontend ainda não (filter(Boolean) sozinho não estreita o tipo em TS).
  const selected = profile.kpis
    .map((metric) => byMetric[metric])
    .filter((card): card is KpiCard => card !== undefined);
  if (selected.length > 0) {
    return selected;
  }
  // Sem perfil resolvido (ou nenhuma métrica reconhecida), o conjunto clássico.
  return CLASSIC_METRICS.map((metric) => byMetric[metric]).filter(
    (card): card is KpiCard => card !== undefined,
  );
}
