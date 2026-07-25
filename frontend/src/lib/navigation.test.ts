import { describe, expect, it } from "vitest";

import { modulesForSegment, visibleNavItems } from "@/lib/navigation";

function routesOf(modules: string[] | null, segment: string | null = null): string[] {
  return visibleNavItems(modules, segment).map((item) => item.to);
}

describe("visibleNavItems", () => {
  it("sempre inclui dashboard e financeiro", () => {
    expect(routesOf([])).toEqual(["", "transactions", "integrations", "plans"]);
  });

  it("habilita itens conforme os módulos do blueprint", () => {
    expect(routesOf(["clients", "appointments"])).toEqual([
      "",
      "transactions",
      "clients",
      "agenda",
      "integrations",
      "plans",
    ]);
  });

  it("qualquer módulo de catálogo habilita Produtos & Serviços", () => {
    expect(routesOf(["inventory"])).toContain("catalog");
    expect(routesOf(["services"])).toContain("catalog");
  });

  it("sem blueprint, mostra os módulos operacionais básicos", () => {
    expect(routesOf(null)).toEqual([
      "",
      "transactions",
      "clients",
      "catalog",
      "employees",
      "integrations",
      "plans",
    ]);
  });

  it("módulos de segmento (assinaturas, projetos, contratos) só aparecem com blueprint", () => {
    expect(routesOf(null)).not.toContain("subscriptions");
    expect(routesOf(["recurring_revenue", "projects", "contracts"])).toEqual(
      expect.arrayContaining(["subscriptions", "projects", "contracts"]),
    );
  });

  it("sem blueprint, adapta a sidebar pelo segmento (barbearia mostra Agenda)", () => {
    const routes = routesOf(null, "Barbearia");
    expect(routes).toEqual(
      ["", "transactions", "clients", "catalog", "employees", "agenda"].concat([
        "integrations",
        "plans",
      ]),
    );
  });

  it("segmento de laboratório (imuno/hemato) habilita Clientes, Serviços e Agenda", () => {
    const routes = routesOf(null, "Laboratório de imunologia e hematologia");
    expect(routes).toContain("clients");
    expect(routes).toContain("catalog");
    expect(routes).toContain("agenda");
  });

  it("segmento de varejo prioriza catálogo/estoque, sem agenda", () => {
    const routes = routesOf(null, "Loja de roupas");
    expect(routes).toContain("catalog");
    expect(routes).not.toContain("agenda");
  });

  it("segmento desconhecido cai nos módulos padrão", () => {
    expect(routesOf(null, "Algo totalmente novo")).toEqual(routesOf(null));
  });
});

describe("modulesForSegment", () => {
  it("casa sem depender de acento ou caixa", () => {
    expect(modulesForSegment("SALÃO de beleza")).toContain("appointments");
    expect(modulesForSegment("estética")).toContain("appointments");
  });

  it("sem segmento, retorna os módulos padrão", () => {
    expect(modulesForSegment(null)).toEqual(["clients", "services", "employees"]);
  });
});
