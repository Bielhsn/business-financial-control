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

**Etapa 22 (Catálogo 2.0):** o `CatalogItem` foi estendido para ficha profissional de
produto (SKU, código de barras, marca, fornecedor, categoria/subcategoria, tags,
descrições curta/completa, custo/promoção, estoque mín/máx/localização, imagens e
variações) **sem quebrar nada existente**: todos os campos novos têm default no documento
Beanie (itens antigos carregam sem migração) e são opcionais na API — um serviço simples
continua sendo nome + preço. Decisões estruturais: variações são **embutidas** no
documento do item (pydantic embutido, não coleção própria) porque só existem no contexto
do produto pai; imagens seguem o mesmo padrão do logo da empresa (data URL `image/*`
validada, ~150 KB, máx. 6 — sem storage externo por enquanto); a margem é **calculada no
servidor** na resposta (`margin_cents`/`margin_pct`, sobre o preço efetivo = promocional
quando houver) e o frontend replica a mesma fórmula só para preview ao vivo no
formulário; unicidade de SKU é verificada por empresa no use case (`find_by_sku`), com
regras compartilhadas de validação (`application/catalog/validation.py`) entre criação e
edição — a edição valida a combinação final (valor novo quando enviado, atual caso
contrário), para promo/custo continuarem coerentes em PATCHes parciais. Ajuste de
quantidade de estoque continua passando exclusivamente por `adjust-stock` (movimentos
auditáveis); o formulário de edição não toca em `stock_quantity`.

**Etapa 21 (integrações inteligentes por segmento):** início da Fase 3 ("inteligência por
segmento"). A decisão estrutural: **nada de mapas fixos segmento → integrações** — isso
quebraria com segmentos em texto livre ("loja de roupas de pet") e exigiria código novo a
cada segmento. Em vez disso, o mecanismo que já é o coração da plataforma foi estendido: o
blueprint ganha `integrations`, selecionadas pela IA de um catálogo fechado
(`INTEGRATION_REGISTRY`, ~60 conectores com grupos), com enum no tool schema + filtro
server-side por `INTEGRATION_IDS` — o mesmo padrão triplo de defesa dos módulos (Etapa 4)
e das métricas de KPI (Etapa 7). O prompt instrui negativamente ("nunca sugira delivery
para quem não vende comida"). Suportar um segmento novo continua não exigindo código;
adicionar um conector novo = uma linha no registro. Blueprints antigos carregam com
`integrations=[]` (default no documento — sem migração) e a página cai no catálogo
completo com um convite a regenerar o blueprint.

**Etapa 20 (polimento premium):** a paleta de comandos (Ctrl/⌘K) é implementação própria
sobre o Dialog existente (~150 linhas) em vez de adicionar `cmdk`: o custo de manter é
menor que o de mais uma dependência com ciclo de vida próprio, e ela consome os mesmos
`NAV_ITEMS` da sidebar — um módulo novo aparece na navegação e na paleta sem tocar em
nenhum dos dois. Abertura por atalho global ou por evento custom
(`openCommandPalette()`), para o botão do header não precisar de estado compartilhado.
PWA: manifest + theme-color tornam o painel instalável; service worker/offline ficou de
fora de propósito — dados financeiros multi-tenant em cache offline são um risco que só
vale correr com requisito real. Microinterações: feedback tátil global nos botões
(`active:scale`) via classe base — um lugar, todos os botões.

**Etapa 19 (plataforma — auditoria persistida + notificações):** a auditoria evoluiu de
log-only (Etapa 12) para **dupla escrita**: `record_audit` grava no log estruturado E na
coleção `audit_logs` (índice composto `company_id + created_at desc`), consultável por
OWNER/ADMIN. O repositório de auditoria recebe `company_id` explícito em vez de usar o
contexto de tenant — a trilha também registra eventos fora de um request tenant-scoped
(ex.: futuros jobs). Notificações são **derivadas, não armazenadas**: o sino computa em
tempo real as contas vencidas/a vencer a partir dos lançamentos PENDING — zero estado
novo para sincronizar (conta paga some da lista sozinha), zero notificações órfãs, e o
custo é uma query que o índice de status já serve. Persistir notificações (com
lido/não-lido, push, e-mail) vira necessário quando houver eventos não-deriváveis —
decisão adiada de propósito. API pública com tokens e webhooks de saída ficam para a
fase de deploy: sem ambiente público, seriam código morto não exercitável.

**Etapa 18 (IA 2.0 — resumo e perguntas):** os dois recursos novos reusam o mesmo
fundamento da Etapa 11 — a IA interpreta agregados que a aplicação computou — mas com
saída em prosa em vez de schema: resumo executivo e resposta a pergunta são texto para
humanos, então tool use forçado não agrega (não há estrutura a garantir); o guard-rail
está no prompt (bloco de números compartilhado + instrução explícita de nunca inventar
valores e de admitir quando os dados não bastam) e no contrato do port, que continua
recebendo somente `DashboardSummary`. O prompt de aterramento é fatorado
(`_grounding_context`) do prompt de insights — uma única fonte dos números para as três
capacidades. A validação da pergunta (mín. 3 caracteres) vive no use case, não só no
schema HTTP — regra de negócio testável independente do transporte.

**Etapa 17 (central de integrações + importação CSV):** a decisão central foi construir
primeiro a **infraestrutura de ingestão** (endpoint de importação em lote) em vez de
conectores específicos: cada integração futura (iFood, Stripe, banco) vira um adaptador
que produz as mesmas linhas normalizadas — e o usuário já resolve hoje qualquer
plataforma que exporte planilha. O parse do CSV acontece no cliente (o backend recebe
JSON tipado e validado pelo Pydantic, nunca arquivo bruto — menos superfície de ataque e
erros de encoding viram problema do parser testado no front). Convenção de extrato:
valor assinado decide o tipo (negativo = despesa) e o backend guarda o valor absoluto.
Categorias são resolvidas por (nome, tipo) com `casefold()` — importar duas planilhas
com "Vendas"/"vendas" não duplica categoria. Datas brasileiras são validadas por
round-trip (o `Date` do JS "rola" 99/99/9999 para uma data real — bug clássico pego por
teste). Limite de 500 linhas por chamada mantém a requisição e o tempo de resposta
previsíveis; arquivos maiores = múltiplos lotes.

**Etapa 16 (customização visual por empresa):** white-label pela mesma alavanca da marca
(Etapa 13): como toda a UI consome tokens (`--primary`, `--ring`...), a cor da empresa é
um `style` com CSS variables no wrapper do shell — sobrescreve a primária só dentro do
painel daquela empresa, sem tocar em landing/login/nada global. O texto sobre a cor
custom é decidido por luminância relativa (WCAG) em `readableForeground` — contraste
garantido para qualquer cor escolhida. Logo como data URL no documento da empresa
(validação dupla: `image/*` + limite de tamanho no schema; nada de servir HTML de
usuário) — um object storage (S3/GCS) é a evolução natural se logos crescerem, mas para
≤150 KB o data URL elimina uma dependência de infraestrutura inteira. Tema padrão da
empresa respeita hierarquia de preferência: escolha manual do usuário > tema da empresa >
sistema — aplicado por efeito com cleanup no unmount, nunca persistido por cima da
escolha do usuário.

**Etapa 15 (sidebar dinâmica completa):** a navegação saiu do componente e virou dado —
`lib/navigation.ts` declara os itens (rota, ícone, módulos que habilitam, core ou não) e
`visibleNavItems(modules | null)` é uma função pura, testada isoladamente, que o
`CompanyLayout` só consome. Decisão de produto embutida: sem blueprint a navegação mostra
os módulos operacionais básicos (clientes, catálogo, funcionários) — IA indisponível
nunca pode significar produto inutilizável. Módulos por segmento sem backend próprio
(agenda, assinaturas, projetos, contratos) ganham rotas estáveis com páginas "em
desenvolvimento" que explicam o que vem e apontam um caminho prático com os módulos
atuais — melhor um caminho honesto do que um item de menu que não faz nada.

**Etapa 14 (onboarding 2.0 + multi-moeda):** `Company` ganhou `currency`,
`sales_channels`, `sales_mode` e `main_offerings` — todos com defaults, então documentos
antigos no Mongo carregam sem migração (schema-on-read do Beanie preenche os defaults
declarados). Esses dados entram no prompt do blueprint: quanto mais contexto real
(canais, forma de venda, o que vende), menos a IA precisa adivinhar a partir só do nome
do segmento. Multi-moeda na apresentação, não no armazenamento: valores continuam
inteiros em centavos agnósticos de moeda; a moeda da empresa só decide a formatação
(`Intl.NumberFormat`) no frontend — conversão cambial entre moedas está explicitamente
fora de escopo (exigiria fonte de cotação e política de data de conversão). Descoberta
importante desta etapa: os testes de API liam o `.env` local — um teste de "IA não
configurada" chegou a chamar a API real da Anthropic quando uma chave apareceu no
ambiente. Corrigido com override de `get_settings` no conftest (`Settings(_env_file=None)`):
a suíte é determinística e nunca depende do ambiente da máquina.

**Etapa 13 (identidade Aurum & landing):** a marca vive inteiramente em tokens: trocar a
identidade da plataforma = trocar as CSS variables em `index.css` (paleta ouro/grafite,
dark "black & gold") e as constantes em `lib/brand.ts` — nenhum componente conhece cores
ou nomes hardcoded. Tipografia de display (Fraunces) via Google Fonts com fallback de
sistema (`ui-serif`): se a fonte não carregar, nada quebra. Logo é SVG inline
(`components/brand/logo.tsx`) — sem asset binário, tema-safe e nítido em qualquer DPI. A
landing é uma rota pública da mesma SPA (lazy, não pesa no app autenticado), com preview
do painel construído em HTML/CSS puro em vez de screenshot — não desatualiza e pesa zero.

**Etapa 12 (hardening final):** `SecurityHeadersMiddleware` (ASGI puro, sem dependência de
`BaseHTTPMiddleware`) injeta em toda resposta: CSP `default-src 'none'; frame-ancestors
'none'` — adequada porque a API nunca serve HTML —, X-Frame-Options DENY,
X-Content-Type-Options nosniff, Referrer-Policy e Permissions-Policy; HSTS só em produção
(em `http://localhost` seria ignorado ou atrapalharia). Corrigida uma lacuna real: a
configuração `CORS_ALLOWED_ORIGINS` existia desde a Etapa 1, mas o `CORSMiddleware` nunca
tinha sido registrado — agora está, com origens restritas, métodos/headers explícitos e
`allow_credentials=False` (autenticação via header Authorization, nunca cookies — CSRF
clássico não se aplica). Auditoria: `audit_event` (structlog, canal "audit") em vez de
coleção no Mongo — a trilha estruturada vai para o destino de logs (imutável no coletor),
não acopla auditoria à disponibilidade do banco e cobre login com sucesso/falha (detecção
de força bruta sem registrar senha nem revelar existência de e-mail), edição de empresa,
geração de blueprint/insights, criação/pagamento/cancelamento de lançamento e ajuste de
estoque; persistência em banco dedicado é evolução natural se houver requisito de
consulta na própria aplicação. i18n ficou como preparação, não implementação: mensagens
de erro centralizadas em exceções semânticas no backend e strings de UI concentradas nos
componentes — extração para catálogos é mecânica quando o requisito chegar.

**Etapa 11 (IA avançada — insights):** separação estrita entre calcular e interpretar. Os
números vêm do `GetDashboardUseCase` (Etapa 7, já testado); a IA recebe **somente
agregados** — receita, despesa, lucro, margem, comparativos, evolução mensal e top
categorias — nunca lançamentos individuais (menos tokens, resposta mais focada e nenhum
dado granular de cliente trafega para o provedor). O prompt instrui explicitamente a não
recalcular nem inventar valores, e a resposta é forçada (`tool_choice`) a um schema com
`kind` em enum fechado (`highlight`/`warning`/`opportunity`), 2–6 itens — mesmo padrão de
IA restrita por catálogo das Etapas 4 e 7. Novo port `InsightsAIPort` no domínio;
`AnthropicAIProvider` implementa os dois ports (blueprint + insights) — um único adapter
de infraestrutura, dois contratos de domínio independentes. O endpoint é POST (não GET):
gerar insights custa tokens e não pode ser disparado por prefetch/refetch automático de
clientes HTTP; restrito a OWNER/ADMIN/MANAGER. Sazonalidade é tratada via evolução mensal
no prompt; previsões ficam como evolução futura (a base — agregados mensais — já existe).
Insights não são persistidos: são interpretação de um retrato do período, recomputáveis a
qualquer momento — persistir criaria estado desatualizável sem benefício claro no MVP.

**Etapa 10 (frontend — dashboard e módulos):** o dashboard consome o endpoint agregado da
Etapa 7 — nenhum cálculo financeiro é refeito no navegador; o frontend só formata
(`formatCents`/`formatPercent`) e desenha. Recharts fica isolado no chunk da página de
dashboard (lazy route) — ~390 kB que só quem abre o dashboard baixa. Entrada de dinheiro:
o usuário digita reais ("1.234,56") e `parseCurrencyToCents` converte para inteiro antes
de qualquer requisição — float de dinheiro não existe em nenhum ponto do fluxo, do input
ao banco. Formulário de cliente renderiza os `client_custom_fields` do blueprint
dinamicamente (a metadata-driven UI completa: a IA definiu os campos no onboarding, o
backend valida as chaves, o frontend gera os inputs). Campos vazios não são enviados —
o backend rejeitaria chaves com valor vazio fora da definição. Mutações invalidam as
queries relacionadas (lançamento novo invalida transações E dashboard), mantendo os
números sempre coerentes sem refetch manual.

**Etapa 9 (frontend — onboarding com IA):** wizard em máquina de estados explícita
(`form → generating → result`, union type discriminada) em vez de flags booleanas soltas —
impossível representar estados inválidos como "gerando sem empresa criada". A geração do
blueprint dispara em `useEffect` na transição de passo (nunca no corpo do componente: o
StrictMode re-renderiza e duplicaria a mutação). Falha de IA não bloqueia o produto: 503
(provedor não configurado) é um estado esperado do wizard — a empresa já foi criada, o
resultado explica e o painel abre mesmo assim; o blueprint pode ser gerado depois. A
importação das categorias sugeridas reusa o endpoint idempotente de seed da Etapa 5. O
catálogo de módulos do backend (`MODULE_REGISTRY`) é espelhado em `lib/modules.ts` para
rotular os módulos na UI — divergência aqui é cosmética (label ausente), nunca funcional,
pois o backend continua sendo a única fonte de verdade sobre módulos válidos.

**Etapa 8 (frontend — fundação):** SPA Vite + React 19 + TypeScript estrito. Tailwind CSS
v4 com tokens de design em CSS variables (`--background`, `--primary`...) e variante
`dark` por classe no `<html>` — o tema é aplicado por um script inline no `index.html`
antes do primeiro paint (sem flash) e gerenciado por um `ThemeProvider`
(claro/escuro/sistema). Componentes de UI no estilo shadcn/ui escritos no repositório
(Radix primitives + CVA), em vez de uma lib de componentes fechada — mesmo racional do
shadcn: os componentes são código nosso, customizáveis sem lutar contra abstrações.
Sessão: access token JWT vive apenas em memória (Zustand); refresh token em
`localStorage` (trade-off documentado: httpOnly cookie exigiria mudar o contrato da API;
mitigado pela rotação a cada uso + revogação server-side). No boot, o refresh token é
trocado por uma sessão nova; um interceptor do axios captura 401, faz um único refresh
(promise compartilhada evita corrida entre N requisições simultâneas) e repete a
requisição. Estado de servidor via React Query (cache/invalidations por
`["companies", id, ...]`); Zustand só para estado global leve. Navegação lateral do shell
é filtrada pelos módulos do Company Blueprint — a "metadata-driven UI" chegando à
interface. Code splitting por rota via `React.lazy` desde já, para o bundle inicial não
crescer com as telas de gráficos. CI ganhou job de frontend (Prettier, ESLint, Vitest,
`tsc -b` + build de produção).

**Etapa 7 (dashboard e indicadores):** os KPIs sugeridos pela IA no blueprint (Etapa 4) até
aqui eram só texto descritivo — sem uma forma de calcular um valor de verdade para eles. Em
vez de deixar isso permanente, `KPIDefinition` ganhou `metric: KPIMetric`, um enum fechado
(`KPI_METRIC_REGISTRY`, em `domain/dashboard/kpi_registry.py`) com as métricas que a
aplicação sabe computar (receita, despesa, lucro, margem, ticket médio, contagem de
lançamentos, clientes ativos). A IA é forçada (`tool_choice`) a associar cada KPI sugerido a
uma dessas métricas — o mesmo padrão de enum controlado já usado para os módulos na Etapa 4,
aplicado agora a indicadores, para impedir que a IA "invente" um KPI que a aplicação não
consegue calcular.

`GetDashboardUseCase` busca os lançamentos pagos **uma única vez**, cobrindo a maior janela
necessária entre o período pedido, o período anterior (para o comparativo) e a janela de
evolução mensal, e deriva todos os agregados em memória a partir dessa lista — uma escolha
deliberada de simplicidade para o volume de uma única empresa nesta etapa; uma pipeline de
agregação do MongoDB (`$match`/`$group` por mês/categoria) é a otimização natural quando o
volume de lançamentos crescer o suficiente para justificar a complexidade adicional. Os
valores computados (receita, despesa, lucro, margem, ticket médio, contagem, clientes
ativos) alimentam tanto o resumo do dashboard quanto os KPIs do blueprint, resolvidos por
`metric` num dicionário — sem blueprint gerado para a empresa, a lista de KPIs computados
fica simplesmente vazia, em vez de falhar. O endpoint (`GET .../dashboard`) é liberado a
qualquer membro da empresa (leitura), sem restrição adicional de papel, na mesma linha da
leitura de categorias e lançamentos.

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
