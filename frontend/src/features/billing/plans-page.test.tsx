/**
 * Tela de planos.
 *
 * O defeito que estes testes travam era caro: "Assinar" chamava a troca de
 * plano, que ativava o Business por 30 dias sem cobrar nada, e "Falar com
 * vendas" liberava o Enterprise inteiro. O produto era gratuito para quem
 * clicasse.
 */
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { PlansPage } from "@/features/billing/plans-page";
import { api } from "@/lib/api";
import { renderScreen } from "@/test/render";

const PLANOS = [
  {
    tier: "starter",
    name: "Starter",
    tagline: "Comece sem custo.",
    target_audience: "MEIs",
    price_cents_monthly: 0,
    price_cents_yearly: 0,
    limits: {
      max_members: 2,
      max_integrations: 1,
      max_ai_insights_per_month: 10,
      max_catalog_items: 50,
    },
    features: [],
    highlights: ["Dashboard essencial"],
    is_contact_sales: false,
    badge: null,
  },
  {
    tier: "professional",
    name: "Profissional",
    tagline: "Para crescer.",
    target_audience: "Pequenos negócios",
    price_cents_monthly: 4900,
    price_cents_yearly: 49000,
    limits: {
      max_members: 5,
      max_integrations: 3,
      max_ai_insights_per_month: 100,
      max_catalog_items: 500,
    },
    features: ["advanced_ai"],
    highlights: ["IA consultora"],
    is_contact_sales: false,
    badge: "Mais popular",
  },
  {
    tier: "enterprise",
    name: "Enterprise",
    tagline: "Sob medida.",
    target_audience: "Redes",
    price_cents_monthly: 49900,
    price_cents_yearly: 499000,
    limits: {
      max_members: -1,
      max_integrations: -1,
      max_ai_insights_per_month: -1,
      max_catalog_items: -1,
    },
    features: ["api_access"],
    highlights: ["Suporte dedicado"],
    is_contact_sales: true,
    badge: null,
  },
];

function assinatura(extra: Record<string, unknown> = {}) {
  return {
    tier: "starter",
    status: "active",
    billing_cycle: "monthly",
    trial_ends_at: null,
    current_period_end: null,
    cancel_at_period_end: false,
    features: [],
    limits: {
      max_members: 2,
      max_integrations: 1,
      max_ai_insights_per_month: 10,
      max_catalog_items: 50,
    },
    usage: { members: 1, integrations: 0 },
    trial_used: false,
    payment_pending: false,
    pending_tier: null,
    ...extra,
  };
}

function mockApi(sub: Record<string, unknown> = assinatura()) {
  vi.spyOn(api, "get").mockImplementation(async (url: string) => {
    if (url.includes("/plans")) return { data: { plans: PLANOS } };
    if (url.includes("/subscription")) return { data: sub };
    return { data: {} };
  });
}

function renderPlans() {
  return renderScreen(<PlansPage />, {
    route: "/c/empresa-1/planos",
    path: "/c/:companyId/planos",
  });
}

/** A tela sai do ar ao contratar; `assign` é o efeito observável. */
function spyOnRedirect() {
  const assign = vi.fn();
  Object.defineProperty(window, "location", {
    configurable: true,
    value: { ...window.location, assign },
  });
  return assign;
}

describe("Planos", () => {
  beforeEach(() => {
    mockApi();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("contratar abre o pagamento em vez de liberar o plano", async () => {
    const assign = spyOnRedirect();
    const post = vi
      .spyOn(api, "post")
      .mockResolvedValue({ data: { payment_url: "https://pagar.test/sub_1" } } as never);
    const put = vi.spyOn(api, "put");
    renderPlans();

    const assinar = await screen.findByRole("button", { name: /assinar/i });
    await userEvent.click(assinar);

    await waitFor(() => expect(assign).toHaveBeenCalledWith("https://pagar.test/sub_1"));
    expect(post).toHaveBeenCalledWith("/companies/empresa-1/billing/checkout", {
      tier: "professional",
      billing_cycle: "monthly",
    });
    // A troca direta de plano é o caminho que dava o produto de graça.
    expect(put).not.toHaveBeenCalled();
  });

  it("o ciclo escolhido acompanha a contratação", async () => {
    spyOnRedirect();
    const post = vi
      .spyOn(api, "post")
      .mockResolvedValue({ data: { payment_url: "https://pagar.test/sub_1" } } as never);
    renderPlans();

    await userEvent.click(await screen.findByRole("button", { name: /anual/i }));
    await userEvent.click(await screen.findByRole("button", { name: /assinar/i }));

    await waitFor(() =>
      expect(post).toHaveBeenCalledWith("/companies/empresa-1/billing/checkout", {
        tier: "professional",
        billing_cycle: "yearly",
      }),
    );
  });

  it("falar com vendas não troca o plano", async () => {
    const put = vi.spyOn(api, "put");
    const post = vi.spyOn(api, "post");
    renderPlans();

    await screen.findByText("Enterprise");
    // Sem endereço de vendas configurado o botão não existe; o que não pode
    // existir é um botão que concede o plano.
    expect(screen.queryByRole("button", { name: /falar com vendas/i })).toBeNull();
    expect(put).not.toHaveBeenCalled();
    expect(post).not.toHaveBeenCalled();
  });

  it("o teste gratuito some depois de usado", async () => {
    mockApi(assinatura({ trial_used: true }));
    renderPlans();

    await screen.findByText("Profissional");
    expect(screen.queryByRole("button", { name: /testar 14 dias/i })).toBeNull();
  });

  it("o teste gratuito é oferecido a quem ainda não usou", async () => {
    renderPlans();
    expect(await screen.findByRole("button", { name: /testar 14 dias/i })).toBeInTheDocument();
  });

  it("pagamento pendente aparece com o caminho para concluir", async () => {
    mockApi(assinatura({ payment_pending: true, pending_tier: "professional" }));
    const assign = spyOnRedirect();
    const post = vi
      .spyOn(api, "post")
      .mockResolvedValue({ data: { payment_url: "https://pagar.test/sub_9" } } as never);
    renderPlans();

    await screen.findByText(/pagamento pendente do plano profissional/i);
    await userEvent.click(screen.getByRole("button", { name: /concluir pagamento/i }));

    await waitFor(() => expect(assign).toHaveBeenCalledWith("https://pagar.test/sub_9"));
    expect(post).toHaveBeenCalled();
  });
});
