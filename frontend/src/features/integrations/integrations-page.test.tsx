/**
 * Fluxo das integrações.
 *
 * O defeito original era a listagem prometer "Disponível" sem oferecer ação.
 * Estes testes travam a regra que substituiu aquilo: o botão aparece em todas,
 * e o que muda é o que o clique entrega — nunca um beco sem saída nem um
 * sucesso falso.
 */
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { IntegrationsPage } from "@/features/integrations/integrations-page";
import { api } from "@/lib/api";
import { renderScreen } from "@/test/render";

const CATALOGO = [
  { id: "hotmart", name: "Hotmart", group: "Infoprodutos", connectable: true, provider: "hotmart" },
  { id: "rappi", name: "Rappi", group: "Delivery", connectable: false, provider: null },
];

const CONECTORES = [
  {
    provider: "hotmart",
    name: "Hotmart",
    group: "Infoprodutos",
    description: "Sincroniza vendas e reembolsos da Hotmart.",
    credential_fields: [
      { key: "client_id", label: "Client ID", secret: false, help_text: null, required: true },
      {
        key: "client_secret",
        label: "Client Secret",
        secret: true,
        help_text: null,
        required: true,
      },
    ],
    capabilities: ["sales"],
    auth_type: "credentials",
  },
];

function mockApi(conexoes: unknown[] = []) {
  vi.spyOn(api, "get").mockImplementation(async (url: string) => {
    if (url.includes("/integrations/catalog")) return { data: { items: CATALOGO } };
    if (url.includes("/connectors/available")) return { data: { connectors: CONECTORES } };
    if (url.includes("/connections")) return { data: conexoes };
    if (url.includes("/segment-profile")) return { data: {} };
    if (url.includes("/blueprint")) return { data: null };
    if (url.includes("/sales-analytics") || url.includes("/analytics/sales")) {
      // Listas vazias, não objeto vazio: o card lê `.length` e um dublê frouxo
      // derrubaria o teste por motivo alheio ao que ele mede.
      return { data: { by_platform: [], top_products: [], peak_hours: [] } };
    }
    return { data: {} };
  });
}

/** Localiza a linha da integração pelo nome e devolve o elemento que tem o botão.
 * Subir a árvore até achar o botão é mais estável que contar `parentElement`. */
async function linhaDaIntegracao(nome: string): Promise<HTMLElement> {
  const rotulo = await screen.findByText(nome);
  let atual: HTMLElement | null = rotulo.parentElement;
  while (atual && atual.querySelectorAll("button").length === 0) {
    atual = atual.parentElement;
  }
  if (!atual) {
    throw new Error(`Nenhum botão na linha de ${nome}`);
  }
  return atual;
}

/** O catálogo completo fica atrás de um <details>; abrir é parte do fluxo. */
async function abrirCatalogoCompleto(user: ReturnType<typeof userEvent.setup>) {
  await user.click(await screen.findByText("Todas as integrações do catálogo"));
}

function renderPage() {
  return renderScreen(<IntegrationsPage />, {
    route: "/c/company-1/integrations",
    path: "/c/:companyId/integrations",
  });
}

beforeEach(() => {
  vi.restoreAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("Integrações", () => {
  it("oferece Conectar mesmo para plataforma sem conector, sem prometer sucesso", async () => {
    // A afordância é uniforme; quem usa não deveria descobrir quais "têm botão".
    const user = userEvent.setup();
    mockApi();
    renderPage();

    await abrirCatalogoCompleto(user);
    const linhaRappi = await linhaDaIntegracao("Rappi");

    await user.click(within(linhaRappi).getByRole("button", { name: /Conectar/ }));

    // Diz o que falta e aponta a alternativa, em vez de falhar em silêncio.
    const modal = await screen.findByRole("dialog");
    expect(within(modal).getByText(/em construção/i)).toBeInTheDocument();
    expect(within(modal).getByText(/CSV/)).toBeInTheDocument();
  });

  it("abre o formulário de credenciais para quem tem conector", async () => {
    const user = userEvent.setup();
    mockApi();
    renderPage();

    await abrirCatalogoCompleto(user);
    const linha = await linhaDaIntegracao("Hotmart");
    await user.click(within(linha).getByRole("button", { name: /Conectar/ }));

    const modal = await screen.findByRole("dialog");
    expect(within(modal).getByLabelText(/Client ID/)).toBeInTheDocument();
    expect(within(modal).getByLabelText(/Client Secret/)).toBeInTheDocument();
  });

  it("envia as credenciais digitadas ao conectar", async () => {
    const user = userEvent.setup();
    mockApi();
    const post = vi.spyOn(api, "post").mockResolvedValue({ data: { provider: "hotmart" } });
    renderPage();

    await abrirCatalogoCompleto(user);
    const linha = await linhaDaIntegracao("Hotmart");
    await user.click(within(linha).getByRole("button", { name: /Conectar/ }));
    const modal = await screen.findByRole("dialog");

    await user.type(within(modal).getByLabelText(/Client ID/), "id-real");
    await user.type(within(modal).getByLabelText(/Client Secret/), "segredo-real");
    await user.click(within(modal).getByRole("button", { name: /Conectar e validar/ }));

    await waitFor(() => expect(post).toHaveBeenCalled());
    const [, corpo] = post.mock.calls[0] as [string, Record<string, unknown>];
    expect(corpo.provider).toBe("hotmart");
    expect(corpo.credentials).toEqual({ client_id: "id-real", client_secret: "segredo-real" });
  });

  it("mostra o estado real quando a conexão existe", async () => {
    mockApi([
      {
        provider: "hotmart",
        status: "connected",
        last_synced_at: "2026-08-20T10:00:00Z",
        last_error: null,
      },
    ]);
    renderPage();

    // O status vem da conexão persistida, não de um rótulo fixo.
    expect(await screen.findByText("Conectada")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Sincronizar/ })).toBeInTheDocument();
  });

  it("mostra o motivo quando o provedor recusou", async () => {
    mockApi([
      {
        provider: "hotmart",
        status: "error",
        last_synced_at: null,
        last_error: "O iFood recusou consultar as vendas (HTTP 403)",
      },
    ]);
    renderPage();

    // Sem o motivo na tela, o lojista não sabe o que corrigir.
    expect(await screen.findByText(/HTTP 403/)).toBeInTheDocument();
  });
});
