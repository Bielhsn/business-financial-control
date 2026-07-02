import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { DashboardPage } from "@/features/dashboard/dashboard-page";
import { api } from "@/lib/api";
import type { DashboardSummaryResponse } from "@/lib/api-types";

const SUMMARY: DashboardSummaryResponse = {
  start: "2026-06-01T00:00:00Z",
  end: "2026-06-30T23:59:59Z",
  revenue_cents: 1500000,
  expense_cents: 500000,
  profit_cents: 1000000,
  profit_margin_pct: 66.7,
  average_ticket_cents: 15000,
  transaction_count: 42,
  active_clients: 12,
  monthly_breakdown: [
    { year: 2026, month: 5, revenue_cents: 1200000, expense_cents: 400000, profit_cents: 800000 },
    { year: 2026, month: 6, revenue_cents: 1500000, expense_cents: 500000, profit_cents: 1000000 },
  ],
  top_income_categories: [{ category_id: "c1", category_name: "Vendas", total_cents: 1500000 }],
  top_expense_categories: [{ category_id: "c2", category_name: "Aluguel", total_cents: 500000 }],
  comparison: { revenue_change_pct: 25, expense_change_pct: 25, profit_change_pct: 25 },
  kpis: [
    {
      key: "average_ticket",
      name: "Ticket médio",
      description: "Valor médio por venda.",
      metric: "average_ticket",
      unit: "cents",
      value: 15000,
    },
  ],
};

// Recharts ResponsiveContainer precisa de dimensões reais — irrelevante para este teste.
vi.mock("recharts", async (importOriginal) => {
  const original = await importOriginal<typeof import("recharts")>();
  return {
    ...original,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  };
});

function renderDashboard() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/c/company-1"]}>
        <Routes>
          <Route path="/c/:companyId" element={<DashboardPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("DashboardPage", () => {
  it("exibe os agregados e KPIs vindos da API", async () => {
    const getSpy = vi.spyOn(api, "get").mockResolvedValue({ data: SUMMARY });
    renderDashboard();

    expect(await screen.findByText("Receita")).toBeInTheDocument();
    expect(screen.getAllByText(/15\.000,00/).length).toBeGreaterThan(0);
    expect(screen.getByText("Ticket médio")).toBeInTheDocument();
    expect(screen.getByText("Principais receitas")).toBeInTheDocument();
    expect(screen.getByText("Vendas")).toBeInTheDocument();
    expect(getSpy).toHaveBeenCalledWith(
      "/companies/company-1/dashboard",
      expect.objectContaining({ params: expect.objectContaining({ months: 6 }) }),
    );
    getSpy.mockRestore();
  });

  it("mostra estado vazio quando não há lançamentos", async () => {
    const getSpy = vi
      .spyOn(api, "get")
      .mockResolvedValue({ data: { ...SUMMARY, transaction_count: 0 } });
    renderDashboard();

    expect(await screen.findByText("Sem lançamentos no período")).toBeInTheDocument();
    getSpy.mockRestore();
  });
});
