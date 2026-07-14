# Frontend — Business Financial Control

SPA em React 19 + TypeScript (strict) + Vite, com Tailwind CSS v4 e componentes no estilo
shadcn/ui (Radix + CVA), tema claro/escuro, React Query para estado de servidor e Zustand
para estado global leve (sessão).

## Rodando

```bash
npm install
npm run dev        # http://localhost:5173 (proxy de /api para localhost:8000)
```

## Scripts

| Script                 | O que faz                                 |
| ---------------------- | ----------------------------------------- |
| `npm run dev`          | Servidor de desenvolvimento com HMR       |
| `npm run build`        | Type check (`tsc -b`) + build de produção |
| `npm run lint`         | ESLint                                    |
| `npm run format`       | Prettier (escrita)                        |
| `npm run format:check` | Prettier (verificação, usado no CI)       |
| `npm test`             | Vitest (jsdom + Testing Library)          |

## Estrutura

```
src/
├── app/            # shell autenticado (layout da empresa, rotas protegidas)
├── components/
│   ├── theme/      # ThemeProvider (claro/escuro/sistema)
│   └── ui/         # componentes base estilo shadcn/ui
├── features/       # por domínio: auth, companies, blueprint...
├── lib/            # axios (refresh automático), tipos da API, utils
├── pages/          # páginas simples/placeholder
└── stores/         # Zustand (sessão)
```

## Autenticação

- Access token JWT vive **apenas em memória** (Zustand) — nunca em storage.
- Refresh token fica em `localStorage` e é **rotacionado a cada uso** pelo backend;
  no boot da aplicação ele é trocado por uma sessão nova (`/auth/refresh`).
- O interceptor do axios tenta um único refresh em respostas 401 e repete a requisição;
  uma promise compartilhada evita corrida entre requisições simultâneas.
