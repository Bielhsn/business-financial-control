import { describe, expect, it } from "vitest";

import { isValidCnpj, maskCnpj, onlyDigits } from "@/lib/cnpj";
import { assessPassword } from "@/lib/password-strength";

describe("maskCnpj", () => {
  it("formata progressivamente enquanto digita", () => {
    expect(maskCnpj("19")).toBe("19");
    expect(maskCnpj("19131")).toBe("19.131");
    expect(maskCnpj("19131243")).toBe("19.131.243");
    expect(maskCnpj("191312430001")).toBe("19.131.243/0001");
    expect(maskCnpj("19131243000197")).toBe("19.131.243/0001-97");
  });

  it("ignora o que não é dígito e não passa de 14", () => {
    expect(maskCnpj("19.131.243/0001-97")).toBe("19.131.243/0001-97");
    expect(onlyDigits(maskCnpj("1913124300019712345"))).toHaveLength(14);
  });
});

describe("isValidCnpj", () => {
  it("aceita CNPJ com dígitos verificadores corretos", () => {
    expect(isValidCnpj("19.131.243/0001-97")).toBe(true);
  });

  it("recusa dígito verificador errado", () => {
    expect(isValidCnpj("19131243000198")).toBe(false);
  });

  it("recusa sequência repetida", () => {
    // Passa na conta dos verificadores e não existe — o descarte é explícito.
    expect(isValidCnpj("00000000000000")).toBe(false);
    expect(isValidCnpj("11111111111111")).toBe(false);
  });

  it("recusa comprimento errado", () => {
    expect(isValidCnpj("191312430001")).toBe(false);
  });
});

describe("assessPassword", () => {
  it("não julga campo vazio", () => {
    expect(assessPassword("")).toMatchObject({ score: 0, hint: "" });
  });

  it("trata senha curta como fraca mesmo com variedade", () => {
    // 8 é o mínimo do servidor; abaixo disso, variedade não compensa.
    const resultado = assessPassword("Aa1!x");
    expect(resultado.strength).toBe("fraca");
    expect(resultado.hint).toContain("8 caracteres");
  });

  it("classifica senha longa e variada como forte, sem dica", () => {
    const resultado = assessPassword("Barbearia2026!");
    expect(resultado.strength).toBe("forte");
    expect(resultado.hint).toBe("");
  });

  it("orienta o que falta nos casos intermediários", () => {
    const resultado = assessPassword("barbearia123");
    expect(resultado.strength).toBe("média");
    expect(resultado.hint).not.toBe("");
  });

  it("senha longa só de minúsculas continua fraca", () => {
    expect(assessPassword("aaaaaaaaaaaa").strength).toBe("fraca");
  });
});
