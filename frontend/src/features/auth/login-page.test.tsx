import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { LoginPage } from "@/features/auth/login-page";
import { api } from "@/lib/api";

function renderLogin() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/login"]}>
        <LoginPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("LoginPage", () => {
  it("mostra erros de validação sem chamar a API", async () => {
    const postSpy = vi.spyOn(api, "post");
    const user = userEvent.setup();
    renderLogin();

    await user.click(screen.getByRole("button", { name: /entrar/i }));

    expect(await screen.findByText("Informe um e-mail válido.")).toBeInTheDocument();
    expect(screen.getByText("Informe sua senha.")).toBeInTheDocument();
    expect(postSpy).not.toHaveBeenCalled();
    postSpy.mockRestore();
  });

  it("envia as credenciais para /auth/login", async () => {
    const postSpy = vi.spyOn(api, "post").mockResolvedValue({
      data: { access_token: "a", refresh_token: "r", token_type: "bearer" },
    });
    const user = userEvent.setup();
    renderLogin();

    await user.type(screen.getByLabelText("E-mail"), "dono@example.com");
    await user.type(screen.getByLabelText("Senha"), "s3cr3t!!");
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    await waitFor(() => {
      expect(postSpy).toHaveBeenCalledWith("/auth/login", {
        email: "dono@example.com",
        password: "s3cr3t!!",
      });
    });
    postSpy.mockRestore();
  });
});
