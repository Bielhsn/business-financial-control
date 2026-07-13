import { describe, expect, it } from "vitest";

import { parseCsv, parseImportCsv } from "@/lib/csv";

describe("parseCsv", () => {
  it("detecta delimitador ponto e vírgula (padrão bancário brasileiro)", () => {
    expect(parseCsv("a;b;c\n1;2;3")).toEqual([
      ["a", "b", "c"],
      ["1", "2", "3"],
    ]);
  });

  it("suporta campos entre aspas com vírgulas e aspas escapadas", () => {
    expect(parseCsv('data,descricao,valor\n01/06/2026,"Almoço, cliente ""VIP""",-50')).toEqual([
      ["data", "descricao", "valor"],
      ["01/06/2026", 'Almoço, cliente "VIP"', "-50"],
    ]);
  });

  it("ignora linhas vazias", () => {
    expect(parseCsv("a;b\n\n1;2\n")).toEqual([
      ["a", "b"],
      ["1", "2"],
    ]);
  });
});

describe("parseImportCsv", () => {
  it("mapeia por cabeçalho e converte valores brasileiros assinados", () => {
    const csv =
      "Data;Descrição;Valor;Categoria\n15/06/2026;PIX recebido;1.500,00;Vendas\n16/06/2026;Aluguel;-2.000,00;Aluguel";
    const result = parseImportCsv(csv);

    expect(result.errors).toEqual([]);
    expect(result.rows).toHaveLength(2);
    expect(result.rows[0]).toMatchObject({
      description: "PIX recebido",
      amount_cents: 150000,
      category_name: "Vendas",
    });
    expect(result.rows[1]).toMatchObject({ amount_cents: -200000 });
  });

  it("aceita CSV sem cabeçalho na ordem data, descrição, valor", () => {
    const result = parseImportCsv("01/06/2026;Venda balcão;100,00");

    expect(result.errors).toEqual([]);
    expect(result.rows[0]).toMatchObject({
      description: "Venda balcão",
      amount_cents: 10000,
      category_name: null,
    });
  });

  it("reporta erros por linha sem descartar as linhas válidas", () => {
    const csv =
      "data;descricao;valor\n99/99/9999;X;10,00\n01/06/2026;Ok;10,00\n01/06/2026;Sem valor;abc";
    const result = parseImportCsv(csv);

    expect(result.rows).toHaveLength(1);
    expect(result.errors).toHaveLength(2);
    expect(result.errors[0]).toContain("Linha 2");
    expect(result.errors[1]).toContain("Linha 4");
  });

  it("aceita datas ISO", () => {
    const result = parseImportCsv("data;descricao;valor\n2026-06-15;Assinatura;49,90");
    expect(result.errors).toEqual([]);
    expect(result.rows[0]!.amount_cents).toBe(4990);
  });
});
