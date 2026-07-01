# Decisões de Arquitetura

Este documento registra as decisões estruturais do projeto e por que foram tomadas. É
atualizado a cada etapa do roadmap (ver `README.md`).

## 1. Monorepo

`backend/` (FastAPI) e `frontend/` (React) no mesmo repositório. Produto único, times
pequenos, versionamento sincronizado. Pode ser desmembrado depois sem custo alto.

## 2. Backend: Clean Architecture (Ports & Adapters)

```
app/
├── core/            # config, logging, exceções, segurança transversal
├── api/v1/          # routers HTTP (camada de entrada)
├── domain/          # entidades, value objects, interfaces (ports) — sem dependência de framework
├── application/     # casos de uso, orquestram domínio + repositórios
├── infrastructure/  # implementações concretas (Mongo, IA, cache, JWT)
└── schemas/         # DTOs Pydantic
```

O domínio depende apenas de interfaces (`Protocol`/ABC); a infraestrutura as implementa.
Isso permite testar regras de negócio sem banco/IA reais e trocar adapters (ex.: provedor
de IA) sem alterar casos de uso — inversão de dependência (SOLID).

**Framework:** FastAPI — async nativo, Pydantic v2 para validação de entrada (segurança),
OpenAPI automático (base para a futura API pública), maturidade e adoção.

**Banco:** MongoDB via Beanie (Motor + Pydantic) — documentos tipados e validados,
queries parametrizadas por construção (mitiga NoSQL injection).

## 3. Multi-tenancy

Banco compartilhado, `company_id` em todo documento tenant-scoped. Um `TenantContext`
(contextvar), populado a partir do JWT após autenticação, é injetado automaticamente
pela camada de repositório em toda leitura/escrita — não depende de cada endpoint lembrar
de filtrar. Evolução futura (cliente enterprise com banco isolado) fica possível sem
reescrever regra de negócio, pois o acesso a dados já passa por uma abstração.

## 4. Dashboard adaptado por segmento — sem geração de código em runtime

A IA não gera código executável. Ela produz um **Company Blueprint** (JSON validado por
schema) a partir das respostas do onboarding: módulos a ativar (de um **Módulo Registry**
pré-construído e testado), categorias financeiras, KPIs e **custom fields** por entidade.
As telas renderizam esses metadados dinamicamente (metadata-driven UI). Isso entrega a
sensação de "dashboard único por empresa" sem os riscos de segurança/qualidade de rodar
código gerado por LLM.

## 5. IA plugável

`AIProviderPort` (interface) no domínio; adapters concretos (`AnthropicAIProvider`,
futuramente outros) na infraestrutura. Provedor inicial: Anthropic Claude API.

## 6. Frontend: feature-based

```
src/
├── app/            # shell, providers, router
├── pages/          # rotas (lazy loaded)
├── features/       # auth, onboarding, dashboard, clients, financial...
├── components/ui/  # shadcn/ui
└── lib/            # axios, query client, utils
```

Organização por feature (não por tipo de arquivo) escala melhor conforme módulos por
segmento crescem. Estado de servidor via React Query; estado global leve (tema, sessão,
empresa ativa) via Zustand.

## 7. Segurança (visão geral — detalhada por etapa)

JWT curto + refresh rotativo, Argon2id para senha, RBAC por papel/módulo, rate limiting,
sanitização de entrada, headers de segurança (CSP, HSTS, X-Frame-Options), CORS restrito,
auditoria de ações sensíveis, criptografia de campos sensíveis em repouso.
