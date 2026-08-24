import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CompleteProfileBanner } from "@/components/complete-profile-banner";
import { renderScreen } from "@/test/render";

describe("CompleteProfileBanner", () => {
  it("leva para as configurações, não para o onboarding", () => {
    // O onboarding CRIA empresa: mandar para lá geraria uma segunda em vez de
    // completar esta. Este teste existe para essa distinção não se perder.
    renderScreen(<CompleteProfileBanner companyId="company-1" />);

    const acao = screen.getByRole("link", { name: /Informar o ramo/ });
    expect(acao).toHaveAttribute("href", "/c/company-1/settings");
  });

  it("explica o que muda ao informar o ramo", () => {
    renderScreen(<CompleteProfileBanner companyId="company-1" />);

    // Sem o porquê, o aviso vira ruído que a pessoa aprende a ignorar.
    expect(screen.getByText(/indicadores, as categorias e os/)).toBeInTheDocument();
  });
});
