import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { CommandPalette, openCommandPalette } from "@/components/command-palette";
import { ThemeProvider } from "@/components/theme/theme-provider";
import { NAV_ITEMS } from "@/lib/navigation";

function LocationProbe() {
  return (
    <Routes>
      <Route path="*" element={null} />
      <Route path="/c/company-1/integrations" element={<p>chegou em integrações</p>} />
    </Routes>
  );
}

function renderPalette() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ThemeProvider>
        <MemoryRouter initialEntries={["/c/company-1"]}>
          <CommandPalette companyId="company-1" navItems={NAV_ITEMS} />
          <LocationProbe />
        </MemoryRouter>
      </ThemeProvider>
    </QueryClientProvider>,
  );
}

describe("CommandPalette", () => {
  it("abre com Ctrl+K, filtra e navega ao selecionar", async () => {
    const user = userEvent.setup();
    renderPalette();

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    const input = await screen.findByLabelText("Buscar página ou ação");

    await user.type(input, "integra");
    const option = await screen.findByRole("option", { name: /Integrações/ });
    await user.click(option.querySelector("button")!);

    await waitFor(() => {
      expect(screen.getByText("chegou em integrações")).toBeInTheDocument();
    });
    // Paleta fecha após executar o comando.
    expect(screen.queryByLabelText("Buscar página ou ação")).not.toBeInTheDocument();
  });

  it("abre via openCommandPalette() (botão do header)", async () => {
    renderPalette();

    openCommandPalette();

    expect(await screen.findByLabelText("Buscar página ou ação")).toBeInTheDocument();
  });
});
