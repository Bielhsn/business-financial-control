import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { OnboardingPage } from "@/features/onboarding/onboarding-page";
import { api } from "@/lib/api";

function renderOnboarding() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/onboarding"]}>
        <OnboardingPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("OnboardingPage", () => {
  it("valida os campos obrigatórios sem chamar a API", async () => {
    const postSpy = vi.spyOn(api, "post");
    const user = userEvent.setup();
    renderOnboarding();

    await user.click(screen.getByRole("button", { name: /criar empresa/i }));

    expect(await screen.findByText("Informe o nome da empresa.")).toBeInTheDocument();
    expect(screen.getByText("Descreva o segmento do negócio.")).toBeInTheDocument();
    expect(postSpy).not.toHaveBeenCalled();
    postSpy.mockRestore();
  });

  it("cria a empresa e dispara a geração do blueprint com IA", async () => {
    const company = {
      id: "company-1",
      name: "Barbearia do Zé",
      segment: "Barbearia",
      employee_count: 3,
      average_customer_count: 100,
      city: "São Paulo",
      state: "SP",
      country: "Brasil",
      size: "Pequena",
      tax_regime: null,
      additional_info: null,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    const blueprint = {
      id: "bp-1",
      company_id: "company-1",
      modules: ["financial_core", "clients"],
      financial_categories: [{ name: "Vendas", type: "income" }],
      kpis: [
        {
          key: "average_ticket",
          name: "Ticket médio",
          description: "Valor médio por venda.",
          metric: "average_ticket",
        },
      ],
      client_custom_fields: [],
      ai_provider: "anthropic",
      generated_at: new Date().toISOString(),
    };
    const postSpy = vi.spyOn(api, "post").mockImplementation(async (url: string) => {
      if (url === "/companies") {
        return { data: company };
      }
      if (url === "/companies/company-1/blueprint") {
        return { data: blueprint };
      }
      throw new Error(`POST inesperado: ${url}`);
    });
    const user = userEvent.setup();
    renderOnboarding();

    await user.type(screen.getByLabelText("Nome da empresa"), "Barbearia do Zé");
    await user.type(screen.getByLabelText("Segmento"), "Barbearia");
    // Radix Select em jsdom: seleciona via teclado no trigger.
    const sizeTrigger = screen.getByRole("combobox", { name: /porte/i });
    await user.click(sizeTrigger);
    await user.click(await screen.findByRole("option", { name: "Pequena" }));
    await user.clear(screen.getByLabelText("Nº de funcionários"));
    await user.type(screen.getByLabelText("Nº de funcionários"), "3");
    await user.clear(screen.getByLabelText("Clientes por mês (média)"));
    await user.type(screen.getByLabelText("Clientes por mês (média)"), "100");
    await user.type(screen.getByLabelText("Cidade"), "São Paulo");
    await user.type(screen.getByLabelText("Estado"), "SP");

    await user.click(screen.getByRole("button", { name: /criar empresa/i }));

    await waitFor(() => {
      expect(postSpy).toHaveBeenCalledWith(
        "/companies",
        expect.objectContaining({ name: "Barbearia do Zé", segment: "Barbearia" }),
      );
    });
    // Resultado do wizard: módulos ativados e categorias sugeridas visíveis.
    expect(await screen.findByText(/criada!/)).toBeInTheDocument();
    expect(screen.getByText("Módulos ativados")).toBeInTheDocument();
    expect(screen.getByText("Vendas")).toBeInTheDocument();
    postSpy.mockRestore();
  });
});
