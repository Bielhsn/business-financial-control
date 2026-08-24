/**
 * Fluxo do lançamento financeiro.
 *
 * Foi nesta tela que apareceu o defeito das modais: um botão auxiliar dentro do
 * formulário submetia o envio e fechava a modal no meio do preenchimento. O
 * teste de unidade do `Button` trava a causa; estes travam o comportamento no
 * lugar onde o usuário sente — com Select, categorias e mutação de verdade.
 *
 * A página é renderizada inteira de propósito. Exportar o diálogo só para o
 * teste alcançá-lo deixaria de fora justamente a composição que quebrou.
 */
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { TransactionsPage } from "@/features/financial/transactions-page";
import { api } from "@/lib/api";
import { renderScreen } from "@/test/render";

const CATEGORIAS = [
  { id: "cat-1", name: "Serviços", type: "income", is_active: true },
  { id: "cat-2", name: "Produtos e insumos", type: "expense", is_active: true },
];

/** Responde por URL — a página consulta vários endpoints ao montar. */
function mockApi() {
  vi.spyOn(api, "get").mockImplementation(async (url: string) => {
    if (url.includes("/financial-categories")) return { data: CATEGORIAS };
    if (url.includes("/transactions")) {
      return { data: { items: [], total: 0, limit: 5, offset: 0 } };
    }
    if (url.includes("/clients")) return { data: [] };
    if (url.includes("/segment-profile")) return { data: {} };
    if (url.includes("/recurring")) return { data: [] };
    if (url.includes("/accounts")) {
      // Forma completa de propósito: um objeto vazio derruba o card de contas,
      // e o teste passaria a falhar por causa do dublê, não do que ele mede.
      return {
        data: {
          payable: { total_cents: 0, overdue_cents: 0, items: [] },
          receivable: { total_cents: 0, overdue_cents: 0, items: [] },
        },
      };
    }
    return { data: {} };
  });
}

function renderPage() {
  return renderScreen(<TransactionsPage />, {
    route: "/c/company-1/financial",
    path: "/c/:companyId/financial",
  });
}

async function abrirNovoLancamento(user: ReturnType<typeof userEvent.setup>) {
  await user.click(await screen.findByRole("button", { name: /Novo lançamento/ }));
  return await screen.findByRole("dialog");
}

beforeEach(() => {
  vi.restoreAllMocks();
  mockApi();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("Lançamento financeiro", () => {
  it("abre a modal de novo lançamento", async () => {
    const user = userEvent.setup();
    renderPage();

    const modal = await abrirNovoLancamento(user);

    expect(within(modal).getByLabelText("Situação")).toBeInTheDocument();
  });

  it('escolher "Já pago/recebido" no select não fecha a modal', async () => {
    // O relato original: interagir com um bloco interno fechava tudo.
    const user = userEvent.setup();
    renderPage();
    const modal = await abrirNovoLancamento(user);

    await user.click(within(modal).getByLabelText("Situação"));
    await user.click(await screen.findByRole("option", { name: /Pendente/ }));

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(within(screen.getByRole("dialog")).getByLabelText("Situação")).toHaveTextContent(
      /Pendente/,
    );
  });

  it("trocar o tipo não fecha a modal e refiltra as categorias", async () => {
    const user = userEvent.setup();
    renderPage();
    const modal = await abrirNovoLancamento(user);

    await user.click(within(modal).getByLabelText("Tipo"));
    await user.click(await screen.findByRole("option", { name: "Despesa" }));

    expect(screen.getByRole("dialog")).toBeInTheDocument();

    // A categoria de receita não pode sobrar num lançamento de despesa.
    await user.click(within(screen.getByRole("dialog")).getByLabelText("Categoria"));
    expect(await screen.findByRole("option", { name: "Produtos e insumos" })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "Serviços" })).not.toBeInTheDocument();
  });

  it("não envia sem categoria e mantém a modal aberta para corrigir", async () => {
    const user = userEvent.setup();
    renderPage();
    const modal = await abrirNovoLancamento(user);
    const post = vi.spyOn(api, "post");

    await user.type(within(modal).getByLabelText("Valor (R$)"), "150,00");
    await user.type(within(modal).getByLabelText("Descrição"), "Corte de cabelo");
    await user.click(within(modal).getByRole("button", { name: /Salvar|Registrar|Criar/ }));

    expect(await screen.findByText("Selecione uma categoria.")).toBeInTheDocument();
    expect(post).not.toHaveBeenCalled();
    // Perder o que foi digitado aqui seria o pior desfecho possível.
    expect(within(screen.getByRole("dialog")).getByLabelText("Descrição")).toHaveValue(
      "Corte de cabelo",
    );
  });

  it("registra o lançamento com o valor convertido para centavos", async () => {
    const user = userEvent.setup();
    renderPage();
    const modal = await abrirNovoLancamento(user);
    const post = vi.spyOn(api, "post").mockResolvedValue({ data: { id: "t-1" } });

    await user.click(within(modal).getByLabelText("Categoria"));
    await user.click(await screen.findByRole("option", { name: "Serviços" }));
    await user.type(within(modal).getByLabelText("Valor (R$)"), "1.234,56");
    await user.type(within(modal).getByLabelText("Descrição"), "Corte + barba");
    await user.click(within(modal).getByRole("button", { name: /Salvar|Registrar|Criar/ }));

    await waitFor(() => expect(post).toHaveBeenCalled());
    const [, corpo] = post.mock.calls[0] as [string, Record<string, unknown>];
    // Dinheiro trafega em centavos inteiros — arredondamento de float aqui vira
    // divergência de caixa.
    expect(corpo.amount_cents).toBe(123456);
    expect(corpo.category_id).toBe("cat-1");
    expect(corpo.description).toBe("Corte + barba");
  });
});
