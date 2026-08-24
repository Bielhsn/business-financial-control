/**
 * Fluxo do cadastro, ponta a ponta na tela.
 *
 * É a maior superfície nova do produto e a porta de entrada de todo cliente: um
 * defeito aqui não degrada uma funcionalidade, impede a conta de existir. Os
 * testes exercitam o que o usuário faz — digitar, sair do campo, enviar — e não
 * o estado interno do formulário.
 */
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { RegisterPage } from "@/features/auth/register-page";
import { api } from "@/lib/api";
import { renderScreen } from "@/test/render";

const CNPJ_VALIDO = "19.131.243/0001-97";

const EMPRESA_DA_RECEITA = {
  cnpj: "19131243000197",
  legal_name: "Empresa Exemplo LTDA",
  trade_name: "Barbearia do Zé",
  status: "ATIVA",
  is_active: true,
  city: "São Paulo",
  state: "SP",
  email: null,
  phone: null,
  main_activity: null,
};

function mockLookup(resposta: unknown = EMPRESA_DA_RECEITA) {
  return vi.spyOn(api, "get").mockResolvedValue({ data: resposta });
}

async function preencherObrigatorios(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText("CNPJ da empresa"), CNPJ_VALIDO);
  await user.type(screen.getByLabelText("Seu nome completo"), "Gabriel Henrique");
  await user.type(screen.getByLabelText("E-mail"), "gabriel@example.com");
  await user.type(screen.getByLabelText("Senha"), "Barbearia2026!");
  await user.type(screen.getByLabelText("Confirme a senha"), "Barbearia2026!");
}

beforeEach(() => {
  vi.restoreAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("Cadastro", () => {
  it("consulta a Receita e preenche o nome da empresa a partir do CNPJ", async () => {
    const user = userEvent.setup();
    const get = mockLookup();
    renderScreen(<RegisterPage />);

    await user.type(screen.getByLabelText("CNPJ da empresa"), CNPJ_VALIDO);

    await waitFor(() => {
      expect(screen.getByLabelText("Nome da empresa")).toHaveValue("Barbearia do Zé");
    });
    // Só os dígitos vão para a API — a máscara é da interface.
    expect(get).toHaveBeenCalledWith("/cnpj/19131243000197");
  });

  it("aplica a máscara enquanto a pessoa digita", async () => {
    const user = userEvent.setup();
    mockLookup();
    renderScreen(<RegisterPage />);

    const campo = screen.getByLabelText("CNPJ da empresa");
    await user.type(campo, "19131243000197");

    expect(campo).toHaveValue("19.131.243/0001-97");
  });

  it("não sobrescreve o nome que a pessoa já escreveu", async () => {
    // Ela pode querer o nome pelo qual o negócio é conhecido, não a razão social.
    const user = userEvent.setup();
    mockLookup();
    renderScreen(<RegisterPage />);

    await user.type(screen.getByLabelText("Nome da empresa"), "Barbearia da Esquina");
    await user.type(screen.getByLabelText("CNPJ da empresa"), CNPJ_VALIDO);

    await waitFor(() => expect(screen.getByText("Barbearia do Zé")).toBeInTheDocument());
    expect(screen.getByLabelText("Nome da empresa")).toHaveValue("Barbearia da Esquina");
  });

  it("não consulta a Receita com CNPJ incompleto ou inválido", async () => {
    const user = userEvent.setup();
    const get = mockLookup();
    renderScreen(<RegisterPage />);

    await user.type(screen.getByLabelText("CNPJ da empresa"), "19131243000198");

    // Dígito verificador errado: gastar a chamada seria desperdício.
    await waitFor(() => expect(get).not.toHaveBeenCalled());
  });

  it("barra o envio quando as senhas não conferem", async () => {
    const user = userEvent.setup();
    mockLookup();
    const post = vi.spyOn(api, "post");
    renderScreen(<RegisterPage />);

    await user.type(screen.getByLabelText("CNPJ da empresa"), CNPJ_VALIDO);
    await user.type(screen.getByLabelText("Seu nome completo"), "Gabriel");
    await user.type(screen.getByLabelText("E-mail"), "gabriel@example.com");
    await user.type(screen.getByLabelText("Senha"), "Barbearia2026!");
    await user.type(screen.getByLabelText("Confirme a senha"), "outra-senha-diferente");
    await user.click(screen.getByRole("button", { name: "Criar conta" }));

    expect(await screen.findByText("As senhas não conferem.")).toBeInTheDocument();
    expect(post).not.toHaveBeenCalled();
  });

  it("mostra a força da senha enquanto digita", async () => {
    const user = userEvent.setup();
    mockLookup();
    renderScreen(<RegisterPage />);

    const senha = screen.getByLabelText("Senha");
    await user.type(senha, "abcdefgh");
    expect(await screen.findByText(/Senha fraca/)).toBeInTheDocument();

    await user.clear(senha);
    await user.type(senha, "Barbearia2026!");
    expect(await screen.findByText(/Senha forte/)).toBeInTheDocument();
  });

  it("envia só os dígitos do CNPJ e a confirmação junto", async () => {
    const user = userEvent.setup();
    mockLookup();
    const post = vi
      .spyOn(api, "post")
      .mockResolvedValue({ data: { id: "1", is_verified: true, email: "gabriel@example.com" } });
    renderScreen(<RegisterPage />);

    await preencherObrigatorios(user);
    await user.click(screen.getByRole("button", { name: "Criar conta" }));

    await waitFor(() => expect(post).toHaveBeenCalled());
    const [rota, corpo] = post.mock.calls[0] as [string, Record<string, unknown>];
    expect(rota).toBe("/auth/register");
    expect(corpo.cnpj).toBe("19131243000197");
    expect(corpo.password_confirmation).toBe("Barbearia2026!");
    expect(corpo.company_name).toBe("Barbearia do Zé");
  });

  it("leva para a confirmação de e-mail quando a conta nasce bloqueada", async () => {
    const user = userEvent.setup();
    mockLookup();
    vi.spyOn(api, "post").mockResolvedValue({
      data: { id: "1", is_verified: false, email: "gabriel@example.com" },
    });
    renderScreen(<RegisterPage />);

    await preencherObrigatorios(user);
    await user.click(screen.getByRole("button", { name: "Criar conta" }));

    // Tentar login aqui falharia — a tela precisa explicar o bloqueio.
    expect(await screen.findByText("confirme seu e-mail")).toBeInTheDocument();
  });

  it("segue para as empresas quando a conta já nasce liberada", async () => {
    const user = userEvent.setup();
    mockLookup();
    vi.spyOn(api, "post").mockImplementation(async (url: string) => {
      if (url === "/auth/register") {
        return { data: { id: "1", is_verified: true, email: "gabriel@example.com" } };
      }
      return { data: { access_token: "tok", refresh_token: "ref" } };
    });
    renderScreen(<RegisterPage />);

    await preencherObrigatorios(user);
    await user.click(screen.getByRole("button", { name: "Criar conta" }));

    expect(await screen.findByText("lista de empresas")).toBeInTheDocument();
  });

  it("a queda da consulta de CNPJ não impede o cadastro", async () => {
    // A verificação que vale é a do servidor; a do formulário é conveniência.
    const user = userEvent.setup();
    vi.spyOn(api, "get").mockRejectedValue(new Error("Receita fora do ar"));
    const post = vi
      .spyOn(api, "post")
      .mockResolvedValue({ data: { id: "1", is_verified: true, email: "gabriel@example.com" } });
    renderScreen(<RegisterPage />);

    await user.type(screen.getByLabelText("CNPJ da empresa"), CNPJ_VALIDO);
    await user.type(screen.getByLabelText("Nome da empresa"), "Barbearia do Zé");
    await user.type(screen.getByLabelText("Seu nome completo"), "Gabriel");
    await user.type(screen.getByLabelText("E-mail"), "gabriel@example.com");
    await user.type(screen.getByLabelText("Senha"), "Barbearia2026!");
    await user.type(screen.getByLabelText("Confirme a senha"), "Barbearia2026!");
    await user.click(screen.getByRole("button", { name: "Criar conta" }));

    await waitFor(() => expect(post).toHaveBeenCalled());
  });
});
