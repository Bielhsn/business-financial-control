import { describe, expect, it } from "vitest";

import { visibleNavItems } from "@/lib/navigation";

function routesOf(modules: string[] | null): string[] {
  return visibleNavItems(modules).map((item) => item.to);
}

describe("visibleNavItems", () => {
  it("sempre inclui dashboard e financeiro", () => {
    expect(routesOf([])).toEqual(["", "transactions"]);
  });

  it("habilita itens conforme os módulos do blueprint", () => {
    expect(routesOf(["clients", "appointments"])).toEqual([
      "",
      "transactions",
      "clients",
      "agenda",
    ]);
  });

  it("qualquer módulo de catálogo habilita Produtos & Serviços", () => {
    expect(routesOf(["inventory"])).toContain("catalog");
    expect(routesOf(["services"])).toContain("catalog");
  });

  it("sem blueprint, mostra os módulos operacionais básicos", () => {
    expect(routesOf(null)).toEqual(["", "transactions", "clients", "catalog", "employees"]);
  });

  it("módulos de segmento (assinaturas, projetos, contratos) só aparecem com blueprint", () => {
    expect(routesOf(null)).not.toContain("subscriptions");
    expect(routesOf(["recurring_revenue", "projects", "contracts"])).toEqual(
      expect.arrayContaining(["subscriptions", "projects", "contracts"]),
    );
  });
});
