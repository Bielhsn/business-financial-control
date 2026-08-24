/**
 * Utilitários para testar telas inteiras, não só funções puras.
 *
 * A cobertura do frontend era rasa perto da do backend, e concentrada em
 * helpers. Foi justamente numa tela — o formulário dentro da modal — que passou
 * um defeito que nenhum teste de unidade pegaria: o botão auxiliar submetia o
 * formulário e fechava a modal no meio do preenchimento.
 *
 * Montar providers à mão em cada arquivo convidaria a divergir (um com retry
 * ligado, outro sem), e teste que falha de vez em quando por causa de retry é
 * pior que teste nenhum.
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, type RenderResult } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

interface RenderOptions {
  /** Rota inicial. Telas que leem `useParams` dependem disso. */
  route?: string;
  /** Caminho declarado da rota, quando a tela lê parâmetros da URL. */
  path?: string;
}

export function renderScreen(ui: ReactElement, options: RenderOptions = {}): RenderResult {
  const { route = "/", path } = options;
  // `retry: false` é essencial: com o padrão, um erro esperado no teste vira
  // três tentativas e o assert corre contra o relógio.
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  const conteudo: ReactNode = path ? (
    <Routes>
      <Route path={path} element={ui} />
      <Route path="*" element={<LocationProbe />} />
    </Routes>
  ) : (
    <>
      {ui}
      <LocationProbe />
    </>
  );

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[route]}>{conteudo}</MemoryRouter>
    </QueryClientProvider>,
  );
}

/** Torna a navegação observável: o teste afirma para onde a tela levou. */
function LocationProbe() {
  return (
    <Routes>
      <Route path="/companies" element={<p>lista de empresas</p>} />
      <Route path="/login" element={<p>tela de login</p>} />
      <Route path="/verifique-email" element={<p>confirme seu e-mail</p>} />
      <Route path="*" element={null} />
    </Routes>
  );
}
