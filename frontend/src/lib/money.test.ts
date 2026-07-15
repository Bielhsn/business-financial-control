import { describe, expect, it } from "vitest";

import { centsToInput, marginPct, parseCurrencyToCents } from "@/lib/money";

describe("parseCurrencyToCents", () => {
  it("aceita formato brasileiro com milhar e decimal", () => {
    expect(parseCurrencyToCents("1.234,56")).toBe(123456);
    expect(parseCurrencyToCents("R$ 1.234,56")).toBe(123456);
    expect(parseCurrencyToCents("0,99")).toBe(99);
  });

  it("aceita formatos sem vírgula", () => {
    expect(parseCurrencyToCents("1234.56")).toBe(123456);
    expect(parseCurrencyToCents("1.234")).toBe(123400);
    expect(parseCurrencyToCents("1500")).toBe(150000);
  });

  it("rejeita entradas inválidas", () => {
    expect(parseCurrencyToCents("")).toBeNull();
    expect(parseCurrencyToCents("abc")).toBeNull();
    expect(parseCurrencyToCents("12,345")).toBeNull();
  });
});

describe("centsToInput", () => {
  it("converte centavos para o formato de edição", () => {
    expect(centsToInput(123456)).toBe("1234,56");
    expect(centsToInput(99)).toBe("0,99");
  });
});

describe("marginPct", () => {
  it("calcula margem sobre o preço de venda", () => {
    expect(marginPct(7990, 3200)).toBe(59.95);
  });

  it("usa o preço promocional quando informado — mesma regra do backend", () => {
    expect(marginPct(7990, 3200, 5990)).toBe(46.58);
  });

  it("retorna null sem custo ou sem preço efetivo positivo", () => {
    expect(marginPct(7990, null)).toBeNull();
    expect(marginPct(0, 3200)).toBeNull();
  });
});
