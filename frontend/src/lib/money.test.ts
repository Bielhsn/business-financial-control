import { describe, expect, it } from "vitest";

import { centsToInput, parseCurrencyToCents } from "@/lib/money";

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
