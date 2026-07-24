import { describe, expect, it } from "vitest";

import { buildWhatsappLink, normalizeBrazilPhone } from "@/lib/whatsapp";

describe("normalizeBrazilPhone", () => {
  it("prefixa 55 em um celular com DDD", () => {
    expect(normalizeBrazilPhone("(11) 99999-8888")).toBe("5511999998888");
  });

  it("mantém o código do país quando já presente", () => {
    expect(normalizeBrazilPhone("+55 11 99999-8888")).toBe("5511999998888");
  });

  it("retorna null para número curto demais ou vazio", () => {
    expect(normalizeBrazilPhone("1234")).toBeNull();
    expect(normalizeBrazilPhone("")).toBeNull();
    expect(normalizeBrazilPhone(null)).toBeNull();
  });
});

describe("buildWhatsappLink", () => {
  it("monta o link wa.me com a mensagem codificada", () => {
    const link = buildWhatsappLink("11999998888", "Olá, João! Bora marcar?");
    expect(link).toBe(
      "https://wa.me/5511999998888?text=Ol%C3%A1%2C%20Jo%C3%A3o!%20Bora%20marcar%3F",
    );
  });

  it("retorna null sem telefone válido", () => {
    expect(buildWhatsappLink(null, "oi")).toBeNull();
  });
});
