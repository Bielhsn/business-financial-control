# Aurum OS

> **Aurum Technologies** · *Inteligência que vale ouro.*

SaaS de gestão empresarial com onboarding assistido por IA: a plataforma interpreta o
segmento de qualquer empresa (existente ou informado livremente pelo usuário) e monta
automaticamente os módulos, categorias financeiras e indicadores adequados àquele
negócio.

## A marca

| | |
|---|---|
| **Empresa** | Aurum Technologies |
| **Produto** | Aurum OS |
| **Slogan** | Inteligência que vale ouro. |
| **Conceito** | *Aurum* é ouro em latim — o produto refina dados brutos da empresa em valor. Estética private-bank: grafite quente + dourado. |
| **Paleta** | Ouro-bronze (primária) · grafite quente (base) · esmeralda (valores positivos) · dark mode "black & gold" |
| **Tipografia** | Fraunces (display/títulos) + Inter (interface) |
| **Missão** | Dar a qualquer empresa a inteligência financeira de uma grande corporação. |
| **Visão** | Ser o sistema operacional de gestão de 1 milhão de PMEs na América Latina. |
| **Valores** | Clareza acima de complexidade · Inteligência acessível · Dados do cliente são do cliente · Design é respeito |

> **Status:** Fases 1, 2 e 3 concluídas — as 24 etapas do roadmap (0-23) estão entregues
> com CI verde. Próximos passos em [Funcionalidades futuras](#funcionalidades-futuras).

## Sumário

- [Visão geral](#visão-geral)
- [Objetivo](#objetivo)
- [Tecnologias utilizadas](#tecnologias-utilizadas)
- [Arquitetura](#arquitetura)
- [Estrutura de pastas](#estrutura-de-pastas)
- [Como executar o projeto](#como-executar-o-projeto)
- [Como executar o backend](#como-executar-o-backend)
- [Como executar o frontend](#como-executar-o-frontend)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Configurando o MongoDB](#configurando-o-mongodb)
- [Guia de contribuição](#guia-de-contribuição)
- [Convenções de código](#convenções-de-código)
- [Estratégia de segurança](#estratégia-de-segurança)
- [Roadmap](#roadmap)
- [Funcionalidades atuais](#funcionalidades-atuais)
- [Funcionalidades futuras](#funcionalidades-futuras)
- [Licença](#licença)

## Visão geral

Hoje existem muitos dashboards financeiros para pessoas físicas, mas praticamente nenhuma
plataforma gera automaticamente um dashboard financeiro personalizado para qualquer
segmento empresarial (tecnologia, barbearia, restaurante, clínica, academia, oficina,
indústria, prestadores de serviço, etc.).

O diferencial deste projeto é o onboarding inteligente: ao cadastrar a empresa, o usuário
responde perguntas simples (segmento, porte, número de funcionários, localização, regime
tributário...) e a IA monta automaticamente a estrutura do dashboard — módulos, telas de
clientes, categorias financeiras e indicadores — adequada àquele tipo de negócio.

## Objetivo

Entregar um sistema multi-tenant, seguro e escalável que:

- Elimina a necessidade de configurar manualmente um dashboard financeiro por segmento.
- Usa IA para interpretar segmentos novos (texto livre) e sugerir a estrutura adequada.
- Mantém isolamento total de dados entre empresas (multi-tenant).
- Nasce pronto para produção: segurança, auditoria, testes e observabilidade desde o início.

## Tecnologias utilizadas

### Frontend

React · TypeScript · Tailwind CSS · React Router · TanStack Query · React Hook Form ·
Zod · Axios · Framer Motion · Recharts · Lucide Icons · shadcn/ui · Zustand

### Backend

Python · FastAPI · Beanie (MongoDB ODM sobre Motor) · Pydantic v2 · JWT · Argon2

### Infraestrutura

MongoDB · Redis · Docker / Docker Compose · GitHub Actions (CI)

### IA

Anthropic Claude API, integrada via uma interface plugável (`AIProviderPort`) que permite
trocar de provedor sem alterar regras de negócio.

## Arquitetura

O backend segue **Clean Architecture** (Ports & Adapters): o domínio (entidades e regras
de negócio) não depende de framework, banco ou provedor de IA — apenas de interfaces.
Infraestrutura (Mongo, IA, cache, segurança) implementa essas interfaces. Isso garante
testabilidade, baixo acoplamento e facilidade para trocar peças (ex.: provedor de IA,
banco) sem reescrever regra de negócio.

O frontend segue organização **feature-based**: cada funcionalidade (auth, onboarding,
dashboard, clientes, financeiro...) é autocontida, com seus próprios componentes, hooks,
chamadas de API e schemas de validação.

O diferencial do produto — dashboard adaptado por segmento — é resolvido sem geração de
código em runtime: a IA produz um **Company Blueprint** (JSON estruturado e validado)
descrevendo quais módulos pré-construídos ativar, categorias financeiras e KPIs; a UI
renderiza isso dinamicamente (metadata-driven UI). Detalhes completos das decisões de
arquitetura, incluindo multi-tenancy e segurança, estão em
[`docs/architecture.md`](docs/architecture.md).

## Estrutura de pastas

```
business-financial-control/
├── backend/
│   ├── app/
│   │   ├── core/            # config, logging, exceções, segurança transversal
│   │   ├── api/v1/          # routers HTTP
│   │   ├── domain/          # entidades, value objects, interfaces (ports)
│   │   ├── application/     # casos de uso
│   │   ├── infrastructure/  # Mongo, IA, cache, JWT (adapters concretos)
│   │   └── schemas/         # DTOs Pydantic
│   ├── tests/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── Dockerfile
├── frontend/                # React 19 + TypeScript + Vite + Tailwind v4
│   ├── src/
│   │   ├── app/             # shell autenticado (layout, rotas protegidas)
│   │   ├── components/      # ui (estilo shadcn/ui) + tema claro/escuro
│   │   ├── features/        # por domínio: auth, companies, blueprint...
│   │   ├── lib/             # axios (refresh automático), tipos da API, utils
│   │   ├── pages/           # páginas simples
│   │   └── stores/          # Zustand (sessão)
│   └── package.json
├── infra/
│   └── docker-compose.yml   # MongoDB + Redis + backend
├── docs/
│   └── architecture.md      # decisões de arquitetura detalhadas
└── .github/workflows/ci.yml
```

## Como executar o projeto

Pré-requisitos: Docker e Docker Compose.

```bash
cp backend/.env.example backend/.env
cd infra
docker compose up --build
```

A API sobe em `http://localhost:8000` (docs interativas em `/docs`). MongoDB fica
disponível em `localhost:27017` e Redis em `localhost:6379`.

## Como executar o backend

Sem Docker, localmente:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Rodar testes e verificações de qualidade:

```bash
pytest --cov=app
ruff check .
black --check .
mypy app
```

## Como executar o frontend

Pré-requisito: Node.js 22+.

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (proxy de /api para localhost:8000)
```

Qualidade e testes:

```bash
npm run lint           # ESLint
npm run format:check   # Prettier
npm test               # Vitest + Testing Library
npm run build          # tsc -b (type check) + build de produção
```

## Variáveis de ambiente

Backend (`backend/.env`, veja `backend/.env.example`):

| Variável                      | Descrição                                                                      |
| ----------------------------- | ------------------------------------------------------------------------------ |
| `ENVIRONMENT`                 | `development`, `staging` ou `production`                                       |
| `API_V1_PREFIX`               | Prefixo das rotas da API (`/api/v1`)                                           |
| `SECRET_KEY`                  | Chave usada na assinatura de tokens — gere um valor forte e único por ambiente |
| `MONGODB_URI`                 | String de conexão do MongoDB                                                   |
| `MONGODB_DB_NAME`             | Nome do banco de dados                                                         |
| `REDIS_URL`                   | String de conexão do Redis (cache, rate limiting)                              |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duração do access token JWT                                                    |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | Duração do refresh token                                                       |
| `CORS_ALLOWED_ORIGINS`        | Origens permitidas, separadas por vírgula                                      |
| `AI_PROVIDER`                 | Provedor de IA ativo (`anthropic`)                                             |
| `ANTHROPIC_API_KEY`           | Chave de API da Anthropic                                                      |

Nunca commite o arquivo `.env` — ele está no `.gitignore`.

## Configurando o MongoDB

- **Via Docker Compose** (recomendado para desenvolvimento): já incluso em
  `infra/docker-compose.yml`, sem configuração adicional.
- **MongoDB local**: instale a versão 7.x e ajuste `MONGODB_URI` em `backend/.env` para
  `mongodb://localhost:27017`.
- **MongoDB Atlas** (produção): crie um cluster, configure IP allowlist/usuário e use a
  connection string fornecida em `MONGODB_URI`.

## Guia de contribuição

1. Crie uma branch a partir de `main`: `feature/<nome-curto>` ou `fix/<nome-curto>`.
2. Siga as [convenções de código](#convenções-de-código).
3. Garanta que `ruff`, `black`, `mypy` e `pytest` passam antes de abrir o PR.
4. Escreva mensagens de commit descritivas (o repositório segue o padrão
   [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`,
   `refactor:`, `docs:`, `test:`, `chore:`).
5. Abra o Pull Request descrevendo o que mudou e por quê.

## Convenções de código

- **Backend:** tipagem estrita (mypy `strict`), formatação com Black, lint com Ruff,
  Clean Architecture (domínio não importa infraestrutura), DTOs Pydantic em todas as
  fronteiras de entrada/saída.
- **Frontend:** TypeScript estrito, componentização por feature, hooks para lógica
  reutilizável, formulários validados com React Hook Form + Zod.
- **Geral:** Clean Code, SOLID, DRY, KISS. Comentários apenas quando o "porquê" não é
  óbvio pelo código.

## Estratégia de segurança

Implementado até a Etapa 3:

- Autenticação via JWT de curta duração (access token) + refresh token opaco, de alta
  entropia, com apenas o hash armazenado no banco — revogável e rotacionado a cada uso.
- Senhas com hash Argon2id (`argon2-cffi`), nunca expostas em nenhuma resposta da API.
- Rate limiting nos endpoints de autenticação (`slowapi`), mitigando força bruta.
- Validação de entrada com Pydantic em todas as rotas (`EmailStr`, tamanho mínimo/máximo
  de senha) e tratamento centralizado de exceções (erros de domínio, validação e HTTP
  nativas convertidos em um formato de resposta consistente, sem vazar detalhes internos).
- Índices únicos no MongoDB (e-mail, hash de refresh token, vínculo usuário-empresa) como
  defesa em profundidade contra condições de corrida, além da checagem em nível de aplicação.
- Isolamento multi-tenant: toda rota de empresa exige um vínculo (`CompanyMembership`)
  validado a cada requisição; usuários sem vínculo recebem 404 (não 403), para não revelar
  a existência de empresas às quais não têm acesso. Um contexto de tenant (contextvar),
  resolvido nessa validação, é consumido automaticamente pelos repositórios de categorias e
  lançamentos financeiros para filtrar/carimbar toda leitura e escrita pela empresa
  correta — impossível de esquecer em um novo endpoint, por construção.
- RBAC por papel (`owner`, `admin`, `manager`, `employee`, `viewer`) via dependência
  reutilizável (`require_role`), usada para restringir edição de empresa e gestão de
  categorias financeiras a papéis de gestão, e lançamentos também à operação (employee).

Concluído no hardening final (Etapa 12):

- Headers de segurança em toda resposta da API: CSP restritiva (`default-src 'none';
  frame-ancestors 'none'` — a API nunca serve HTML), X-Frame-Options DENY (clickjacking),
  X-Content-Type-Options nosniff, Referrer-Policy e Permissions-Policy; HSTS emitido
  apenas em produção.
- CORS efetivamente restrito às origens configuradas (`CORS_ALLOWED_ORIGINS`), com
  métodos e headers explícitos e `allow_credentials=False` (a autenticação usa o header
  Authorization, nunca cookies).
- Trilha de auditoria estruturada (`audit_event` via structlog, JSON em produção) para
  ações sensíveis: registro/login (sucesso e falha — detecção de força bruta), edição de
  empresa, geração de blueprint e de insights por IA, criação/pagamento/cancelamento de
  lançamentos e ajustes de estoque.
- No frontend: access token só em memória, refresh token rotacionado a cada uso e
  revogado no logout.

Planejado como evolução futura:

- Criptografia de campos sensíveis em repouso e upload de arquivos validado por conteúdo.
- Internacionalização (i18n) — as mensagens já são centralizadas, facilitando extração.

Detalhes de implementação de cada mecanismo são documentados em
[`docs/architecture.md`](docs/architecture.md) conforme cada etapa do roadmap é concluída.

## Roadmap

| #   | Etapa                                                                                    | Status       |
| --- | ---------------------------------------------------------------------------------------- | ------------ |
| 0   | Fundação do monorepo (estrutura, tooling, Docker Compose, CI)                            | ✅ Concluída |
| 1   | Backend core (config, logging, exceções, conexão com o banco, health check)              | ✅ Concluída |
| 2   | Autenticação e usuários (JWT, refresh token, Argon2, rate limiting)                      | ✅ Concluída |
| 3   | Multi-tenant e empresas (modelo Company, isolamento por tenant, papéis)                  | ✅ Concluída |
| 4   | Onboarding com IA (Company Blueprint: módulos, categorias, KPIs)                         | ✅ Concluída |
| 5   | Módulo financeiro core (fluxo de caixa, contas a pagar/receber, categorias)              | ✅ Concluída |
| 6   | Módulos dinâmicos (clientes com custom fields, produtos/serviços, estoque, funcionários) | ✅ Concluída |
| 7   | Dashboard e indicadores financeiros                                                      | ✅ Concluída |
| 8   | Frontend — fundação (Vite, Tailwind, shadcn/ui, tema claro/escuro, autenticação)         | ✅ Concluída |
| 9   | Frontend — onboarding com IA (wizard)                                                    | ✅ Concluída |
| 10  | Frontend — dashboard e telas dos módulos                                                 | ✅ Concluída |
| 11  | IA avançada (insights automáticos, sazonalidade, base para previsões)                    | ✅ Concluída |
| 12  | Hardening final (testes completos, auditoria, revisão de segurança, i18n)                | ✅ Concluída |

### Fase 2 — de projeto a produto

| #   | Etapa                                                                    | Status       |
| --- | ------------------------------------------------------------------------ | ------------ |
| 13  | Identidade Aurum & landing page pública                                  | ✅ Concluída |
| 14  | Onboarding 2.0 (moeda, canais de venda, forma de venda) + multi-moeda    | ✅ Concluída |
| 15  | Sidebar dinâmica completa e novos módulos por segmento                   | ✅ Concluída |
| 16  | Customização visual por empresa (logo, cor, tema — white-label light)    | ✅ Concluída |
| 17  | Central de Integrações + importação CSV/OFX de lançamentos               | ✅ Concluída |
| 18  | IA 2.0 (resumo do mês, perguntas sobre a empresa, metas, anomalias)      | ✅ Concluída |
| 19  | Plataforma (auditoria persistida + notificações; API pública futura)     | ✅ Concluída |
| 20  | Polimento premium (microinterações, command palette, PWA)                | ✅ Concluída |

### Fase 3 — inteligência por segmento

| #   | Etapa                                                                    | Status       |
| --- | ------------------------------------------------------------------------ | ------------ |
| 21  | Integrações inteligentes por segmento (IA seleciona do catálogo)         | ✅ Concluída |
| 22  | Catálogo 2.0 — produto profissional (imagens, variações, SKU, margens)   | ✅ Concluída |
| 23  | IA consultora (sinais de estoque/vendas/clientes + recomendações)        | ✅ Concluída |
| 24  | Agenda — agendamentos com receita automática ao concluir                 | ✅ Concluída |
| 25  | Conectores externos (arquitetura modular) + Hotmart → financeiro          | ✅ Concluída |
| 26  | Cadastro de empresa completo + validação/autopreenchimento de CNPJ        | ✅ Concluída |
| 27  | Autenticação completa (verificação e-mail, reset/troca senha, Google)     | ✅ Concluída |
| 28  | Convites de equipe (papéis) + LGPD (exportar/excluir dados)               | ✅ Concluída |
| 29  | Planos de assinatura (Starter/Professional/Business/Enterprise) + gating  | ✅ Concluída |

## Funcionalidades atuais

- Estrutura do monorepo, tooling de qualidade (Ruff, Black, mypy) e CI configurados.
- Esqueleto do backend em Clean Architecture com endpoint inicial e testes automatizados.
- Ambiente de desenvolvimento via Docker Compose (MongoDB + Redis + API).
- Configuração tipada via `pydantic-settings`, com validação que impede rodar em produção
  com segredo padrão.
- Logging estruturado (`structlog`): JSON em produção, formato legível em desenvolvimento.
- Tratamento centralizado de exceções (`AppError` e subclasses semânticas), convertendo
  erros de domínio, de validação e não tratados em respostas HTTP consistentes.
- Conexão assíncrona com MongoDB via `pymongo` (driver assíncrono nativo) + Beanie, com
  inicialização/encerramento no ciclo de vida da aplicação e `GET /api/v1/health` reportando
  o status do banco.
- Autenticação completa: cadastro (`POST /api/v1/auth/register`), login com emissão de
  access token JWT + refresh token opaco e revogável (`POST /api/v1/auth/login`), rotação
  de refresh token (`POST /api/v1/auth/refresh`), logout com revogação (`POST
/api/v1/auth/logout`) e usuário autenticado (`GET /api/v1/auth/me`). Senhas com Argon2id;
  rate limiting nos endpoints de autenticação.
- Multi-tenant: cadastro de empresas (`POST /api/v1/companies`, com os campos do
  onboarding: segmento, porte, número de funcionários, localização, regime tributário
  etc.), listagem das empresas do usuário com seu papel (`GET /api/v1/companies`), consulta
  (`GET /api/v1/companies/{id}`) e atualização restrita a OWNER/ADMIN
  (`PATCH /api/v1/companies/{id}`). Isolamento por empresa garantido por um contexto de
  tenant resolvido e validado a cada requisição (usuário precisa ter vínculo com a empresa
  do path); RBAC básico por papel (owner, admin, manager, employee, viewer).
- Onboarding com IA: `POST /api/v1/companies/{id}/blueprint` (restrito a OWNER/ADMIN) usa a
  Anthropic API para interpretar o segmento e os dados da empresa e gerar um **Company
  Blueprint** — módulos a ativar (de um catálogo pré-construído), categorias financeiras,
  KPIs relevantes e campos personalizados para o cadastro de clientes. `GET
.../blueprint` consulta o blueprint já gerado. Sem `ANTHROPIC_API_KEY` configurada, o
  endpoint responde 503 de forma explícita em vez de falhar de forma confusa.
- Módulo financeiro core: categorias financeiras (`POST/GET/PATCH .../financial-categories`,
  com importação idempotente das sugestões do blueprint via
  `POST .../financial-categories/seed-from-blueprint`), lançamentos financeiros
  (`POST/GET/PATCH .../transactions`) que servem tanto de contas a pagar/receber
  (pendentes, com vencimento) quanto de fluxo de caixa realizado (uma vez marcados como
  pagos via `POST .../transactions/{id}/mark-paid`; cancelamento apenas de pendentes via
  `.../cancel`), e um resumo de fluxo de caixa por período (`GET .../cash-flow`). Valores
  em centavos (inteiro), como na API do Stripe — evita erros de arredondamento de ponto
  flutuante. RBAC: gestão de categorias restrita a OWNER/ADMIN/MANAGER; lançamentos também
  liberados a EMPLOYEE; leitura liberada a qualquer membro. Todo dado financeiro é
  automaticamente filtrado/carimbado pela empresa do contexto de tenant atual na camada de
  repositório — o código de aplicação nunca precisa (nem consegue) esquecer o filtro.
- Módulos dinâmicos: clientes (`.../clients`) com campos personalizados validados contra
  os sugeridos pelo Company Blueprint (chaves fora da lista são rejeitadas), incluindo um
  resumo de relacionamento (`.../clients/{id}/summary`) com valor total gasto, quantidade
  de compras e última compra — calculado a partir dos lançamentos financeiros pagos
  vinculados ao cliente. Catálogo unificado de produtos e serviços (`.../catalog-items`,
  campo `kind`: `product` ou `service`) — produtos podem controlar estoque, serviços não;
  ajuste de estoque (`.../catalog-items/{id}/adjust-stock`) é atômico no banco (`$inc`) e
  gera um registro de auditoria (`StockMovement`) a cada ajuste. Funcionários
  (`.../employees`) com cadastro simples. RBAC: cadastro de clientes e lançamento de
  vendas/ajuste de estoque liberados também a EMPLOYEE (operação do dia a dia); gestão de
  catálogo e funcionários restrita a OWNER/ADMIN/MANAGER; leitura liberada a qualquer
  membro.
- Dashboard financeiro (`GET .../dashboard?start=...&end=...&months=...`, liberado a
  qualquer membro): receita, despesa, lucro e margem do período; ticket médio e contagem
  de lançamentos; clientes ativos (distintos, com compra paga no período); evolução
  mensal de receita/despesa/lucro numa janela configurável (1 a 24 meses); top 5
  categorias de receita e de despesa; comparativo percentual com o período anterior de
  mesma duração; e os KPIs sugeridos pela IA no Company Blueprint, agora com valores
  calculados de verdade — cada KPI sugerido é associado pela IA a uma métrica computável
  de um catálogo fixo (`KPIMetric`), a mesma estratégia de enum controlado já usada para os
  módulos, evitando que a IA "invente" indicadores que a aplicação não sabe calcular.
- Frontend — fundação: SPA em React 19 + TypeScript estrito + Vite, Tailwind CSS v4 com
  design tokens (tema claro/escuro/sistema sem flash no primeiro paint), componentes no
  estilo shadcn/ui (Radix + CVA), React Query, Zustand e code splitting por rota. Telas de
  login/registro validadas com React Hook Form + Zod, sessão com access token só em
  memória + refresh token rotacionado (interceptor axios renova em 401 e repete a
  requisição), seleção de empresas com papel do usuário, e shell autenticado cuja navegação
  lateral é filtrada pelos módulos do Company Blueprint. Job próprio no CI (Prettier,
  ESLint, Vitest, `tsc -b` + build).
- Frontend — onboarding com IA: wizard de criação de empresa em etapas animadas
  (dados do negócio → geração do blueprint com IA → resultado). O formulário aceita
  segmento em texto livre; ao criar a empresa, o blueprint é gerado automaticamente e o
  resultado mostra módulos ativados, categorias financeiras sugeridas (com importação em
  um clique), KPIs e campos personalizados de cliente. Se o provedor de IA não estiver
  configurado (503), o fluxo degrada com elegância: a empresa é criada e o painel abre
  mesmo assim.
- Frontend — dashboard e telas dos módulos: dashboard com seletor de período (mês, 30/90
  dias, ano), cards de receita/despesa/lucro com comparativo percentual vs. período
  anterior, KPIs do blueprint com valores reais, evolução mensal em gráfico (Recharts,
  isolado em chunk próprio via code splitting) e top categorias. Telas completas de
  lançamentos (novo lançamento com valor em reais convertido para centavos, filtros,
  marcar como pago/cancelar, gestão de categorias com importação das sugestões da IA),
  clientes (formulário com campos personalizados dinâmicos do blueprint e resumo de
  relacionamento por cliente), produtos & serviços (catálogo unificado com ajuste de
  estoque auditado) e funcionários. Navegação do shell condicionada aos módulos do
  blueprint.
- Insights financeiros por IA: `POST /api/v1/companies/{id}/insights` (restrito a
  OWNER/ADMIN/MANAGER) gera de 2 a 6 insights (destaques, alertas e oportunidades) sobre
  o período — a IA recebe **apenas os agregados já computados** pelo dashboard (nunca
  lançamentos individuais) e é forçada via tool use a responder em formato estruturado
  com tipos de um enum fechado; ela interpreta os números, nunca os calcula. Endpoint é
  POST deliberadamente: consome tokens e não deve disparar por refetch automático. No
  dashboard, card "Insights da IA" com geração sob demanda e degradação graciosa quando
  o provedor não está configurado.

- Hardening final: security headers em todas as respostas (CSP, X-Frame-Options,
  nosniff, Referrer-Policy, Permissions-Policy, HSTS em produção), CORS restrito às
  origens configuradas e trilha de auditoria estruturada para ações sensíveis (logins com
  sucesso/falha, edição de empresa, geração de blueprint/insights, lançamentos e ajustes
  de estoque). Suíte final: 227 testes no backend (90% de cobertura) + 15 no frontend.

- Onboarding 2.0 e multi-moeda: o cadastro da empresa agora captura moeda de operação
  (ISO 4217), canais de venda, forma de venda e principais produtos/serviços — tudo
  alimenta o prompt do blueprint, deixando a personalização por segmento bem mais
  precisa. Toda a interface formata valores na moeda da empresa ativa (R$, US$, €, £...),
  mantendo centavos inteiros por baixo. Campos novos são opcionais com defaults: empresas
  já criadas continuam funcionando sem migração.

- Sidebar dinâmica completa: a navegação agora cobre todos os módulos do catálogo
  (Agenda, Assinaturas, Projetos, Contratos, além dos já funcionais) e é derivada de uma
  função pura testada (`visibleNavItems`) — com blueprint, mostra exatamente o que a IA
  ativou para o segmento; sem blueprint, mostra os módulos operacionais básicos para o
  produto não travar sem IA. Módulos ainda sem backend têm páginas próprias com URL
  estável, badge "em desenvolvimento" e uma sugestão prática de como resolver hoje com os
  módulos existentes.

- Customização visual por empresa (white-label light): cada empresa pode definir logo
  (upload de imagem até 150 KB, armazenada como data URL validada — só `image/*`), cor
  primária (hex validado, com contraste do texto calculado automaticamente por
  luminância WCAG) e tema padrão. A cor sobrescreve os tokens de primária apenas dentro
  do shell da empresa via CSS variables; o tema padrão da empresa vale só para usuários
  que seguem a preferência do sistema — nunca sobrescreve escolha manual. Página de
  configurações com presets, color picker e prévia ao vivo; salvar é restrito a
  OWNER/ADMIN no backend.

- Central de Integrações + importação CSV: novo módulo "Integrações" na navegação com
  o catálogo de conectores planejados (iFood, Stripe, Mercado Pago, bancos, Omie, CRMs…)
  e a **importação de extrato CSV funcionando de verdade**: parser próprio com suporte a
  campos entre aspas e detecção de delimitador (`;` bancário ou `,`), mapeamento por
  cabeçalho (data/descrição/valor/categoria) ou posicional, valores brasileiros
  assinados (negativo = despesa), validação linha a linha com relatório de erros e
  prévia antes de confirmar. No backend, `POST .../transactions/import` (até 500 linhas)
  cria categorias sob demanda (dedupe case-insensitive) e audita a importação.

- IA 2.0: dois novos recursos no dashboard, ambos alimentados apenas pelos agregados já
  computados (a IA nunca calcula nem vê lançamentos individuais). **Resumo executivo**
  (`POST .../insights/summary`): o período narrado em um parágrafo direto — resultado, o
  que pesou, tendência. **Pergunte à Aurum** (`POST .../insights/ask`): perguntas em
  linguagem natural ("por que meu lucro caiu?", "onde estou gastando mais?") respondidas
  estritamente a partir dos números do período; quando os dados não bastam, a IA diz
  isso e sugere o que registrar. Ambos restritos a papéis de gestão e auditados.

- Plataforma: a trilha de auditoria agora é **persistida e consultável** — as ações
  sensíveis gravam em `audit_logs` (além do log estruturado) e OWNER/ADMIN consultam em
  `GET .../audit-logs`, com "Atividade recente" nas configurações da empresa. Central de
  **notificações in-app**: sino no topo com contas vencidas e a vencer nos próximos 7
  dias — derivadas em tempo real dos lançamentos pendentes (nada é armazenado: conta
  paga some sozinha, sem estado lido/não-lido para sincronizar). API pública com tokens
  e webhooks de saída ficam para a fase de deploy (exigem ambiente público para serem
  úteis).

- Polimento premium: paleta de comandos (Ctrl/⌘K) com navegação e ações por teclado
  (filtragem, setas, Enter — implementação própria sobre o Dialog, sem dependência
  extra), microinteração tátil nos botões, manifest PWA (instalável, tema "black &
  gold") e botão de busca no header. A navegação da paleta é derivada da mesma fonte da
  sidebar — módulos novos aparecem nos dois lugares automaticamente.

- Integrações inteligentes por segmento: o blueprint agora inclui as **integrações
  relevantes para o negócio**, escolhidas pela IA de um catálogo fechado de ~60
  conectores (`INTEGRATION_REGISTRY` — delivery, e-commerce, marketplaces, logística,
  pagamentos, bancos, fiscal, agendamento, fitness, saúde, CRM, comunicação, analytics).
  Uma loja de roupas vê Shopify/Nuvemshop/Melhor Envio; um restaurante vê iFood/KDS; um
  SaaS vê Stripe/Mixpanel/GitHub — sem nenhum código por segmento: a IA interpreta o
  segmento (inclusive texto livre) e seleciona do catálogo, com filtro server-side
  contra ids inventados. A página de Integrações destaca as recomendadas e recolhe o
  restante do catálogo.

- Catálogo 2.0 — cadastro profissional de produtos: SKU (com unicidade por empresa),
  código de barras, marca, fornecedor, categoria/subcategoria, tags, descrições curta e
  completa, múltiplas imagens (até 6, com principal, reordenação e exclusão), variações
  (cor/tamanho com SKU, preço e estoque próprios), preço de custo e promocional com
  margem calculada no servidor, estoque mínimo/máximo com alerta visual e localização
  física. Tudo opcional: um serviço simples continua sendo só nome + preço.

- IA consultora — o sistema calcula sinais de negócio deterministicamente (estoque
  zerado, estoque abaixo do mínimo, margem apertada, queda de receita vs. média dos
  meses anteriores, contas pendentes vencidas) e mostra tudo no dashboard sem custo de
  IA; com um clique, a IA prioriza os sinais e escreve recomendações práticas para a
  semana — sempre a partir dos números computados, nunca inventando valores.

- Agenda — agendamentos com data/hora, duração, cliente, profissional (funcionário) e
  serviço do catálogo (nome e preço herdados dele), navegação por dia e status
  marcado/concluído/cancelado/faltou. Ao concluir um agendamento com preço, um lançamento
  de receita PAID é gerado automaticamente na categoria "Atendimentos", vinculado ao
  cliente — de forma idempotente (concluir de novo não duplica a receita). O módulo é
  ativado pela IA para segmentos de serviço (barbearia, salão, clínica etc.).

- Conectores externos (arquitetura modular) — uma porta `Connector` + registro
  (`CONNECTOR_REGISTRY`) + factory tornam a adição de um provedor uma questão de escrever
  uma classe e registrar uma linha, sem mexer no motor de sync, na API ou no frontend. As
  credenciais são validadas na conexão e guardadas **criptografadas** (Fernet). O primeiro
  conector é a **Hotmart** (OAuth2 client-credentials): sincroniza vendas e reembolsos e os
  materializa como lançamentos financeiros idempotentes (via `external_ref` — re-sincronizar
  nunca duplica), alimentando dashboard, fluxo de caixa e relatórios. A página de
  Integrações permite conectar, sincronizar e desconectar; o formulário de credenciais é
  gerado dinamicamente a partir do registro.

- Cadastro de empresa completo + CNPJ — a empresa passa a ter razão social, nome fantasia,
  CNPJ, subsegmento, faturamento médio mensal, telefone, e-mail, site e redes sociais
  (tudo opcional, sem quebrar empresas já criadas). Os dígitos do CNPJ são validados
  localmente (mesmo algoritmo da Receita) e, com um clique em **Buscar**, o sistema
  consulta a BrasilAPI para **autopreencher** razão social, nome fantasia, contato e situação
  cadastral (avisando se não estiver ativa). Editável em Configurações → Dados da empresa.

- Autenticação completa — além de login/registro com JWT + refresh e Argon2 (já existentes),
  a plataforma passa a ter verificação de e-mail por código de 6 dígitos, recuperação de
  senha ("esqueci minha senha" → código → nova senha), alteração de senha (encerrando as
  demais sessões) e login com Google (OAuth). Exigir e-mail confirmado no login é uma flag
  (`REQUIRE_EMAIL_VERIFICATION`, desligada por padrão). Códigos ficam com hash e expiração;
  o envio usa uma porta de e-mail (adaptador de console em dev, SMTP/provedor em produção).

- Convites de equipe + LGPD — cada empresa pode ter vários usuários com papéis
  (proprietário, administrador, gerente, funcionário, visualizador). Proprietários e
  administradores convidam por e-mail (quem já tem conta entra na hora; quem não tem recebe
  um convite pendente que vira acesso ao criar a conta e aceitar), alteram papéis e removem
  membros — sempre preservando ao menos um proprietário. LGPD: o proprietário pode exportar
  todos os dados da empresa em JSON (sem segredos de integração) e excluir a empresa
  permanentemente (com confirmação pelo nome), apagando todos os dados relacionados.

- Planos de assinatura — catálogo com quatro níveis (Starter grátis, Professional, Business e
  Enterprise), cada um com preço mensal/anual sugerido, público-alvo, limites (usuários,
  integrações, insights de IA, itens de catálogo) e funcionalidades incluídas. O catálogo é a
  fonte única da verdade (`app/domain/subscription/plans.py`) e alimenta a página de preços, o
  cálculo de direitos (entitlements) e o _gating_. Cada empresa tem uma assinatura própria
  (ativa, em teste de 14 dias, inadimplente ou cancelada); sem assinatura ou ao cancelar, cai
  para o Starter. O proprietário faz upgrade/downgrade, inicia teste e cancela pela tela
  "Plano". Recursos além do plano são bloqueados com HTTP 402 e uma mensagem que convida ao
  upgrade — por exemplo, conectar mais integrações ou convidar mais membros do que o plano
  permite. A cobrança real (Stripe) entra numa etapa futura; por ora a troca de plano é
  registrada imediatamente para alimentar o painel administrativo (MRR, trials, renovações).

## Funcionalidades futuras

- Telas de clientes, produtos, serviços, estoque, funcionários e dashboard, adaptadas
  conforme os módulos e campos personalizados do Company Blueprint de cada empresa.
- Insights financeiros gerados por IA, detecção de sazonalidade e previsões.
- Internacionalização, múltiplas moedas, temas, API pública e aplicativo mobile.

## Licença

Todos os direitos reservados. Licenciamento definitivo a ser definido pelo mantenedor do
projeto.
