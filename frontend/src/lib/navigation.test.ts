import { describe, expect, it } from "vitest";

import { GENERIC_SEGMENT_PROFILE } from "@/lib/segment";
import { visibleNavItems } from "@/lib/navigation";

function routesOf(modules: string[]): string[] {
  return visibleNavItems(modules).map((item) => item.to);
}

describe("visibleNavItems", () => {
  it("sempre inclui dashboard, financeiro, integrações e plano", () => {
    expect(routesOf([])).toEqual(["", "transactions", "integrations", "plans"]);
  });

  it("habilita itens conforme os módulos do segmento", () => {
    expect(routesOf(["clients", "appointments"])).toEqual([
      "",
      "transactions",
      "clients",
      "agenda",
      "integrations",
      "plans",
    ]);
  });

  it("qualquer módulo de catálogo habilita a tela de itens", () => {
    expect(routesOf(["inventory"])).toContain("catalog");
    expect(routesOf(["services"])).toContain("catalog");
  });

  it("uma operação só de produtos não mostra agenda", () => {
    // Loja de bebidas: produtos e estoque, sem agendamento.
    expect(routesOf(["clients", "products", "inventory"])).not.toContain("agenda");
  });

  it("renomeia os itens com a terminologia do segmento", () => {
    const clinicTerminology = {
      ...GENERIC_SEGMENT_PROFILE.terminology,
      clients: "Pacientes",
      catalog: "Procedimentos & Exames",
      employees: "Profissionais",
      agenda: "Consultas",
    };
    const labels = visibleNavItems(
      ["clients", "services", "employees", "appointments"],
      clinicTerminology,
    ).map((item) => item.label);

    expect(labels).toContain("Pacientes");
    expect(labels).toContain("Procedimentos & Exames");
    expect(labels).toContain("Consultas");
    expect(labels).not.toContain("Clientes");
  });

  it("sem terminologia, mantém os rótulos padrão", () => {
    const labels = visibleNavItems(["clients"]).map((item) => item.label);
    expect(labels).toContain("Clientes");
  });
});
