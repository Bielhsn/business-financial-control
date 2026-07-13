import { describe, expect, it } from "vitest";

import { cn, formatCents, formatPercent, readableForeground } from "@/lib/utils";

describe("cn", () => {
  it("mescla classes e resolve conflitos do tailwind", () => {
    expect(cn("p-2", "p-4")).toBe("p-4");
    const hidden = false as boolean;
    expect(cn("text-sm", hidden && "hidden", "font-medium")).toBe("text-sm font-medium");
  });
});

/** Intl usa espaço não separável (U+00A0) entre "R$" e o valor — normaliza para comparar. */
function normalize(value: string): string {
  return value.replace(/\u00a0/g, " ");
}

describe("formatCents", () => {
  it("formata centavos como moeda brasileira", () => {
    expect(normalize(formatCents(150000))).toBe("R$ 1.500,00");
    expect(normalize(formatCents(-9900))).toBe("-R$ 99,00");
    expect(normalize(formatCents(0))).toBe("R$ 0,00");
  });
});

describe("formatPercent", () => {
  it("inclui sinal positivo e uma casa decimal", () => {
    expect(formatPercent(12.34)).toBe("+12,3%");
    expect(formatPercent(-4)).toBe("-4,0%");
    expect(formatPercent(0)).toBe("0,0%");
  });
});

describe("readableForeground", () => {
  it("usa texto claro sobre cores escuras e escuro sobre cores claras", () => {
    expect(readableForeground("#1c1917")).toBe("#ffffff"); // grafite
    expect(readableForeground("#B45309")).toBe("#ffffff"); // ouro-bronze
    expect(readableForeground("#FDE68A")).toBe("#1c1917"); // ouro claro
    expect(readableForeground("#ffffff")).toBe("#1c1917");
  });
});
