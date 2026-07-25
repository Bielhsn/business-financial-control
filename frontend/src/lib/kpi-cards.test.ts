import { describe, expect, it } from "vitest";

import type { DashboardSummaryResponse, SegmentProfileResponse } from "@/lib/api-types";
import { buildKpiCards } from "@/lib/kpi-cards";
import { GENERIC_SEGMENT_PROFILE } from "@/lib/segment";

const DATA: DashboardSummaryResponse = {
  start: "2026-07-01",
  end: "2026-07-31",
  revenue_cents: 500_000,
  expense_cents: 200_000,
  profit_cents: 300_000,
  profit_margin_pct: 60,
  average_ticket_cents: 5_000,
  transaction_count: 100,
  active_clients: 42,
  monthly_breakdown: [],
  top_income_categories: [],
  top_expense_categories: [],
  comparison: {
    revenue_change_pct: 10,
    expense_change_pct: -5,
    profit_change_pct: 20,
  } as DashboardSummaryResponse["comparison"],
  kpis: [],
};

function profileWith(overrides: Partial<SegmentProfileResponse>): SegmentProfileResponse {
  return { ...GENERIC_SEGMENT_PROFILE, ...overrides };
}

describe("buildKpiCards", () => {
  it("mostra os indicadores que o perfil elegeu, na ordem definida", () => {
    const barbershop = profileWith({
      kpis: ["total_revenue", "transaction_count", "average_ticket", "active_clients"],
      terminology: { ...GENERIC_SEGMENT_PROFILE.terminology, transactions: "Atendimentos" },
    });

    const titles = buildKpiCards(barbershop, DATA, "BRL").map((card) => card.title);

    expect(titles).toEqual(["Receita", "Atendimentos", "Ticket médio", "Clientes ativos"]);
  });

  it("usa o vocabulário do segmento nos rótulos", () => {
    const clinic = profileWith({
      kpis: ["transaction_count", "active_clients"],
      terminology: {
        ...GENERIC_SEGMENT_PROFILE.terminology,
        transactions: "Atendimentos",
        clients: "Pacientes",
      },
    });

    const titles = buildKpiCards(clinic, DATA, "BRL").map((card) => card.title);

    expect(titles).toEqual(["Atendimentos", "Pacientes ativos"]);
  });

  it("varejo vê margem e vendas, não indicadores de atendimento", () => {
    const store = profileWith({
      kpis: ["total_revenue", "profit_margin", "transaction_count"],
      terminology: { ...GENERIC_SEGMENT_PROFILE.terminology, transactions: "Vendas" },
    });

    const cards = buildKpiCards(store, DATA, "BRL");

    expect(cards.map((c) => c.title)).toContain("Margem de lucro");
    expect(cards.map((c) => c.title)).toContain("Vendas");
    expect(cards.find((c) => c.key === "profit_margin")?.value).toBe("60%");
  });

  it("sem KPIs no perfil, mantém o conjunto clássico", () => {
    const titles = buildKpiCards(profileWith({ kpis: [] }), DATA, "BRL").map((c) => c.title);
    expect(titles).toEqual(["Receita", "Despesas", "Lucro", "Clientes ativos"]);
  });

  it("ignora métrica desconhecida sem quebrar a tela", () => {
    const cards = buildKpiCards(profileWith({ kpis: ["nao_existe", "profit"] }), DATA, "BRL");
    expect(cards.map((c) => c.key)).toEqual(["profit"]);
  });
});
