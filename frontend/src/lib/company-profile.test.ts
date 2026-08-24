import { describe, expect, it } from "vitest";

import { isProfileIncomplete } from "@/lib/company-profile";

describe("isProfileIncomplete", () => {
  it("aponta incompleto quando o segmento está vazio", () => {
    // É assim que toda empresa nasce no cadastro em um passo.
    expect(isProfileIncomplete({ segment: "" })).toBe(true);
  });

  it("trata segmento só com espaços como vazio", () => {
    expect(isProfileIncomplete({ segment: "   " })).toBe(true);
  });

  it("não aponta nada enquanto a empresa carrega", () => {
    // Afirmar incompletude aqui faria o aviso piscar na tela a cada navegação.
    expect(isProfileIncomplete(undefined)).toBe(false);
  });

  it("considera completo quando o ramo foi informado", () => {
    expect(isProfileIncomplete({ segment: "Barbearia" })).toBe(false);
  });
});
