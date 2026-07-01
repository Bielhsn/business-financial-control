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

**Etapa 3 (multi-tenant e empresas):** `Company` é o tenant raiz; um usuário pode
pertencer a várias empresas, cada uma com um papel (`CompanyRole`: owner, admin, manager,
employee, viewer) via `CompanyMembership` — por isso o papel não fica no JWT (o usuário
pode trocar de empresa sem refazer login) nem embutido em `User`. Rotas com `{company_id}`
no path resolvem e validam o vínculo a cada requisição via `get_company_context`
(`api/v1/deps.py`): sem vínculo, 404 (não 403 — evita revelar a existência da empresa a
quem não tem acesso). Essa validação também popula `core/tenant.py` (`ContextVar`), que
`get_current_company_id()` expõe para os repositórios de dados por empresa das próximas
etapas — chamando essa função sem contexto resolvido levanta `RuntimeError`
propositalmente (falha visível de programação, nunca retorno silencioso de dados de todas
as empresas). `require_role(*roles)` é uma dependência-fábrica que compõe
`get_company_context` para restringir ações por papel (hoje usada em `PATCH
/companies/{id}`, restrito a OWNER/ADMIN). `CreateCompanyUseCase` cria a empresa e o
vínculo OWNER em duas escritas sequenciais com ação compensatória (excluir a empresa) se o
vínculo falhar — não é uma transação multi-documento real, o que exigiria um MongoDB em
modo replica set (Atlas sempre é; um único `mongod` de desenvolvimento não é por padrão);
avaliar transações reais quando a Etapa 5 (financeiro) precisar de atomicidade mais forte.

**Etapa 2 (autenticação):** camada de domínio com `User`/`RefreshToken` (dataclasses) e
interfaces `UserRepository`, `RefreshTokenRepository`, `PasswordHasher`, `TokenService`;
casos de uso em `application/auth` (registro, login, refresh, logout) dependem apenas
dessas interfaces — testados com fakes em memória, sem precisar de banco real. Infra:
`Argon2PasswordHasher` (argon2-cffi) e `JWTTokenService` (PyJWT) implementam os ports;
`BeanieUserRepository`/`BeanieRefreshTokenRepository` persistem em Mongo. Access token JWT
de curta duração; refresh token é uma string opaca de alta entropia, com apenas o hash
(SHA-256) armazenado — permite revogação real (JWT sozinho não seria revogável) e é
rotacionado a cada uso. Rate limiting (slowapi) nos endpoints de auth, armazenamento em
memória por padrão (suficiente para uma instância; pronto para migrar para Redis via
`storage_uri=settings.redis_url` em deploys com múltiplas instâncias). Também corrigido:
`register_exception_handlers` passou a tratar `HTTPException`/`StarletteHTTPException`
genericamente (cobre `RateLimitExceeded` do slowapi e qualquer 404/405 nativo do
Starlette), fechando uma lacuna da Etapa 1 em que essas exceções escapavam do formato de
erro padronizado.

**Etapa 1 (core):** `core/config.py` centraliza toda configuração tipada (falha ao subir
em produção com `SECRET_KEY` padrão); `core/logging.py` configura `structlog` (JSON em
produção, console legível em desenvolvimento); `core/exceptions.py` define `AppError` e
subclasses semânticas (`NotFoundError`, `ValidationError`, `UnauthorizedError`,
`ForbiddenError`, `ConflictError`) convertidas em respostas HTTP consistentes por
`register_exception_handlers`; `infrastructure/database/mongodb.py` gerencia o ciclo de
vida da conexão (conectar no startup, fechar no shutdown) e expõe `ping_database()`,
consumido por `GET /api/v1/health`. A aplicação falha ao subir se o MongoDB estiver
inacessível no startup — fail-fast deliberado para não rodar com uma dependência crítica
quebrada.

**Framework:** FastAPI — async nativo, Pydantic v2 para validação de entrada (segurança),
OpenAPI automático (base para a futura API pública), maturidade e adoção.

**Banco:** MongoDB via Beanie sobre o driver assíncrono nativo do `pymongo` (Motor está em
processo de descontinuação pela MongoDB em favor dessa API nativa, e a versão atual do
Beanie já assume `pymongo.AsyncMongoClient`) — documentos tipados e validados, queries
parametrizadas por construção (mitiga NoSQL injection).

## 3. Multi-tenancy

Banco compartilhado, `company_id` em todo documento tenant-scoped. Como um usuário pode
pertencer a várias empresas, o `company_id` ativo não vem do JWT (que só identifica o
usuário) — é resolvido a partir do path da requisição e validado contra o vínculo
(`CompanyMembership`) do usuário logado (ver Etapa 3 abaixo). Essa validação popula um
contextvar (`core/tenant.py`) que será consumido automaticamente pela camada de
repositório em toda leitura/escrita de dados por empresa a partir da Etapa 5/6 — não
depende de cada endpoint lembrar de filtrar. Evolução futura (cliente enterprise com banco
isolado) fica possível sem reescrever regra de negócio, pois o acesso a dados já passa por
uma abstração.

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
