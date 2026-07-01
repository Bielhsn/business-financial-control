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

**Etapa 6 (módulos dinâmicos):** `Client` ganha `custom_fields: dict[str, str]`, validados
em `CreateClientUseCase`/`UpdateClientUseCase` contra as chaves definidas em
`blueprint.client_custom_fields` (Etapa 4) — sem blueprint gerado, nenhum campo
personalizado é aceito; chaves fora da lista são rejeitadas com `ValidationError`. Essa é a
"metadata-driven UI" prometida desde a Etapa 0 chegando ao backend: o frontend (Etapa 8+)
poderá renderizar o formulário de cliente dinamicamente a partir do mesmo blueprint que
valida essas chaves aqui.

`FinancialTransaction` ganhou `client_id` opcional, conectando o módulo financeiro ao de
clientes sem precisar de um novo "módulo de vendas": `GetClientSummaryUseCase` deriva valor
total gasto, quantidade de compras e última compra a partir dos lançamentos `PAID`
vinculados ao cliente — em vez de armazenar esses agregados de forma denormalizada (o que
exigiria mantê-los sincronizados a cada novo lançamento).

Produtos e serviços foram unificados em uma única entidade (`CatalogItem`, campo `kind`)
em vez de dois modelos quase idênticos — evita duplicar CRUD para "coisas vendáveis com
preço", um padrão comum em sistemas de ponto de venda. Ajuste de estoque
(`AdjustStockUseCase` + `CatalogItemRepository.adjust_stock`) usa `$inc`/`$set` atômicos do
MongoDB (via `beanie.operators.Inc/Set`) para evitar a condição de corrida clássica de
leitura-then-escrita em ajustes concorrentes; a validação de "não pode ficar negativo",
porém, ainda lê o valor antes de ajustar — uma janela de corrida residual aceitável no
volume de uma única empresa, documentada no código (`AdjustStockUseCase`). Toda mudança de
estoque gera um `StockMovement` (auditoria), e atualizações de item comuns
(`UpdateCatalogItemUseCase`) não têm permissão de tocar `stock_quantity` diretamente — só o
fluxo de ajuste, para não furar essa trilha de auditoria.

RBAC introduz uma distinção nova: operação do dia a dia (registrar cliente, vender/ajustar
estoque) liberada também a `EMPLOYEE`, mas gestão estrutural (catálogo, funcionários)
restrita a `OWNER`/`ADMIN`/`MANAGER` — o mesmo padrão já usado para lançamentos financeiros
na Etapa 5.

**Etapa 5 (financeiro core):** primeiro consumidor real do contexto de tenant descrito na
Etapa 3 — `core/tenant.get_current_company_id()` deixa de ser só infraestrutura pronta e
passa a ser usado por `BeanieFinancialCategoryRepository`/`BeanieFinancialTransactionRepository`
em toda operação (carimba `company_id` ao criar, filtra por ele em toda leitura/atualização),
sem que a camada de aplicação precise passar `company_id` explicitamente — se uma
dependência de contexto de empresa não foi resolvida antes, `get_current_company_id()`
levanta `RuntimeError` em vez de silenciosamente devolver dados de todas as empresas.

Modelo único de lançamento (`FinancialTransaction`) para contas a pagar/receber e fluxo de
caixa, em vez de dois modelos separados: um lançamento nasce `PENDING` (com `due_date`) ou
já `PAID` (com `paid_at`, para registrar algo que já aconteceu); contas a pagar/receber são
uma visão filtrada por `status=PENDING`, fluxo de caixa realizado é uma visão filtrada por
`status=PAID`. Cancelamento (`CancelTransactionUseCase`) só é permitido em lançamentos
`PENDING` — reverter um lançamento já pago exigiria um estorno/ajuste próprio para não
corromper o histórico de caixa, fora do escopo desta etapa.

Valores monetários são armazenados como inteiro na menor unidade da moeda (`amount_cents`,
como a API do Stripe) em vez de `Decimal`: o driver `pymongo`/Beanie não serializa
`decimal.Decimal` para BSON automaticamente, e `float` teria erros de arredondamento —
inteiro evita as duas classes de problema com zero ambiguidade, ao custo de expor
"centavos" em vez de "reais" na API (decisão registrada para quem for construir o
frontend).

Categorias financeiras (`FinancialCategory`) agora existem como registros reais e
gerenciáveis (diferente da sugestão da IA, que é só um `SuggestedFinancialCategory`
embutido no blueprint) — `SeedFinancialCategoriesFromBlueprintUseCase` importa as sugestões
como categorias reais, comparando por nome+tipo para ser idempotente (rodar de novo não
duplica). RBAC: gestão de categorias e o próprio seed exigem papel de gestão (OWNER/ADMIN/
MANAGER, seed restrito a OWNER/ADMIN por ser uma ação estrutural); lançamentos do dia a dia
também liberados a EMPLOYEE; leitura (categorias, lançamentos, fluxo de caixa) liberada a
qualquer membro.

**Etapa 4 (onboarding com IA):** `domain/blueprint/module_registry.py` define um catálogo
fixo de módulos (`financial_core`, `clients`, `products`, `inventory`, `employees`,
`appointments`, `projects`, `contracts`, `recurring_revenue`, `dashboard`...) — a IA nunca
inventa módulos fora dessa lista, apenas escolhe entre eles (reforçado tecnicamente: o
schema da tool call usada na Anthropic API restringe `modules` a um `enum` com esses ids;
e `_parse_blueprint` filtra qualquer id fora do catálogo como defesa em profundidade
adicional). `AIProviderPort` (domínio) define o contrato; `AnthropicAIProvider`
(infraestrutura) implementa usando a Anthropic API com **tool use forçado**
(`tool_choice={"type": "tool", ...}`), garantindo que a resposta seja sempre um JSON
estruturado e validável, nunca texto livre a ser interpretado (elimina uma classe inteira
de bugs de parsing e reduz superfície de prompt injection, já que a saída não é
executada como código). O resultado (`CompanyBlueprintDraft`) é persistido em
`company_blueprints` (1:1 com a empresa, upsert a cada regeneração). Sem
`ANTHROPIC_API_KEY` configurada, `get_ai_provider` (dependência) recusa a requisição com
503 explícito — sem fallback heurístico "de mentirinha", para não criar uma segunda
implementação a manter. Geração restrita a OWNER/ADMIN via `require_role`, reaproveitando
a infraestrutura de RBAC da Etapa 3; consulta (`GET`) liberada a qualquer membro.

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
contextvar (`core/tenant.py`), consumido automaticamente pela camada de repositório em toda
leitura/escrita de dados por empresa (categorias e lançamentos financeiros desde a Etapa 5,
demais módulos de negócio seguirão o mesmo padrão) — não depende de cada endpoint lembrar
de filtrar. Evolução futura (cliente enterprise com banco
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
