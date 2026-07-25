# Deploy — Aurum OS

Duas formas de colocar o Aurum OS em produção:

- **A. Render + Vercel + Atlas (gerenciado, grátis para começar)** — backend na
  Render, frontend na Vercel e MongoDB no Atlas. Veja a seção "Deploy gerenciado".
- **B. Servidor próprio com Docker** — a stack completa (frontend nginx, backend,
  MongoDB e Redis) sobe com um comando. Veja da seção 1 em diante.

---

## Deploy gerenciado (Render + Vercel + Atlas)

**Backend (Render)** — Web Service a partir do repositório GitHub:

- **Root Directory**: `backend` (o `Dockerfile` fica dentro dela).
- **Branch**: `main`.
- Variáveis de ambiente mínimas: `ENVIRONMENT=production`, `SECRET_KEY` forte,
  `MONGODB_URI` (string `mongodb+srv://...` do Atlas), `MONGODB_DB_NAME`,
  `MONGODB_SERVER_SELECTION_TIMEOUT_MS=15000`, `PUBLIC_BASE_URL` (a URL do
  próprio serviço na Render), `APP_BASE_URL` (a URL do frontend na Vercel, usada
  para montar os LINKS de confirmação de e-mail e redefinição de senha) e
  `CORS_ALLOWED_ORIGINS` (a URL do frontend na Vercel). Para exigir e-mail
  confirmado antes do primeiro login, ligue `REQUIRE_EMAIL_VERIFICATION=true` (e
  configure o envio real de e-mails, abaixo). Opcionais: `PLATFORM_ADMIN_EMAILS`,
  `EMAIL_PROVIDER=resend` + `RESEND_API_KEY` + `EMAIL_FROM`, `GOOGLE_CLIENT_ID`,
  `ANTHROPIC_API_KEY`.
- No **MongoDB Atlas**: usuário/senha em *Database Access* e liberação de IP
  (`0.0.0.0/0`) em *Network Access*.
- Verificação: `https://SEU-BACKEND.onrender.com/api/v1/health` →
  `{"status":"ok","database":"ok"}`.

**Frontend (Vercel)** — importe o repositório GitHub na Vercel:

- **Root Directory**: `frontend` (a Vercel detecta Vite e configura build/output
  sozinha).
- O `frontend/vercel.json` já faz o **proxy de `/api/*` para o backend na
  Render** (mesma origem no navegador — sem CORS) e o fallback de SPA para o
  React Router. Se a URL do seu backend for outra, ajuste o `destination` nele.
- Opcional: `VITE_GOOGLE_CLIENT_ID` nas variáveis de ambiente do projeto Vercel
  (habilita o botão "Entrar com Google"; exige também `GOOGLE_CLIENT_ID` no
  backend).
- Cada merge na `main` redeploya o frontend automaticamente.

> **Plano grátis da Render:** o serviço "dorme" após inatividade — a primeira
> requisição pode levar ~1 minuto (cold start). Os planos pagos removem isso.

---

## Deploy com Docker (servidor próprio)

A stack é composta por quatro serviços: **frontend** (nginx servindo o SPA),
**backend** (FastAPI), **MongoDB** e **Redis**.

O único serviço exposto ao mundo é o **frontend** (porta 80), que faz proxy de
`/api` para o backend. Banco e cache ficam apenas na rede interna do compose.

---

## 1. Pré-requisitos

- Docker e Docker Compose v2 no servidor.
- Um domínio apontando para o servidor (para HTTPS — veja a seção 5).

## 2. Configurar os segredos

Copie o exemplo e preencha com **segredos fortes** (nunca reutilize os de dev):

```bash
cp backend/.env.example backend/.env
```

Mínimo obrigatório em produção:

| Variável | O que é |
| --- | --- |
| `ENVIRONMENT` | `production` (obriga um `SECRET_KEY` forte) |
| `SECRET_KEY` | 32+ bytes aleatórios (`openssl rand -hex 32`) |
| `CONNECTOR_SECRET_KEY` | chave Fernet dedicada (`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`) |
| `CORS_ALLOWED_ORIGINS` | a URL pública do frontend (ex.: `https://app.suaempresa.com`) |
| `PUBLIC_BASE_URL` | a URL pública da API para os callbacks OAuth (ex.: `https://app.suaempresa.com`) |
| `APP_BASE_URL` | a URL pública do frontend, usada nos LINKS de confirmação de e-mail e reset de senha (ex.: `https://app.suaempresa.com`) |

`MONGODB_URI` e `REDIS_URL` **não** precisam ser definidos no `.env` — o
`docker-compose.prod.yml` já os aponta para os serviços internos.

Opcionais (habilitam funcionalidades): `PLATFORM_ADMIN_EMAILS` (painel admin),
`ANTHROPIC_API_KEY` (IA), `GOOGLE_CLIENT_ID` (login Google),
`EMAIL_PROVIDER=resend` + `RESEND_API_KEY` + `EMAIL_FROM` (e-mails reais de
verificação de conta e reset de senha), `*_CLIENT_ID`/`*_CLIENT_SECRET`
(integrações OAuth).

> **E-mails em produção:** por padrão `EMAIL_PROVIDER=console` só imprime o
> código no log (dev). A confirmação de e-mail e o reset de senha chegam por
> LINK — defina `APP_BASE_URL` com a URL do frontend para os links apontarem
> para o site certo. Para enviar de verdade, crie uma conta no
> [Resend](https://resend.com), valide um domínio de envio, gere uma API Key e
> configure `EMAIL_PROVIDER=resend`, `RESEND_API_KEY=re_...` e um `EMAIL_FROM`
> desse domínio (ex.: `Aurum OS <no-reply@suaempresa.com>`).

> **Nunca** faça commit do `backend/.env` — ele já está no `.gitignore`.

## 3. Subir a stack

```bash
docker compose -f infra/docker-compose.prod.yml up -d --build
```

- O frontend fica em `http://SEU_SERVIDOR/`.
- Verifique a saúde da API: `http://SEU_SERVIDOR/api/v1/health` → `{"status":"ok","database":"ok"}`.
- Logs: `docker compose -f infra/docker-compose.prod.yml logs -f backend`.

## 3.1. Criar a conta de dono (super-admin)

Com a stack no ar, crie a sua conta de dono já pronta para logar. Rode o script
de bootstrap uma vez (escolha uma senha forte — ela não fica gravada em lugar
nenhum, só é mostrada no terminal):

```bash
docker compose -f infra/docker-compose.prod.yml exec \
    -e ADMIN_PASSWORD='sua-senha-forte' \
    backend python -m scripts.create_admin --email voce@suaempresa.com
```

- Se a conta não existe, ela é criada **verificada** (loga direto).
- Se já existe, o script garante que está ativa/verificada e troca a senha.

Para liberar o **painel super-admin** (`/admin`, com MRR/ARR, churn, etc.),
inclua o mesmo e-mail em `PLATFORM_ADMIN_EMAILS` no `backend/.env` e reinicie o
backend. O script avisa se isso ainda não está configurado.

## 3.2. Tarefas agendadas (recorrências)

Os lançamentos recorrentes (aluguel, salários, assinaturas) são materializados
por um job de manutenção idempotente. Agende-o num **cron externo** — por
exemplo, uma vez por dia às 6h:

```bash
0 6 * * *  docker compose -f /caminho/infra/docker-compose.prod.yml exec -T \
    backend python -m scripts.run_scheduled
```

O job percorre todas as empresas e gera as recorrências vencidas de cada uma.
Rodar de novo não duplica (idempotente por `external_ref`). Preferimos um cron
externo a um scheduler embutido para não duplicar a execução quando o backend
roda com múltiplos workers.

## 4. Atualizações

```bash
git pull
docker compose -f infra/docker-compose.prod.yml up -d --build
```

Os volumes `mongo_data` e `redis_data` são preservados entre deploys.

## 5. HTTPS (recomendado)

Coloque um proxy TLS na frente (Caddy, Traefik ou nginx + certbot). Exemplo
rápido com Caddy (`Caddyfile`):

```
app.suaempresa.com {
    reverse_proxy localhost:80
}
```

Ao usar HTTPS, ajuste `CORS_ALLOWED_ORIGINS` e `PUBLIC_BASE_URL` para `https://…`.

## 6. Backups

Faça backup periódico do MongoDB:

```bash
docker compose -f infra/docker-compose.prod.yml exec mongo \
    mongodump --archive=/data/db/backup-$(date +%F).archive
```

Copie o arquivo para fora do servidor (S3, etc.). Restauração: `mongorestore --archive=...`.

## 7. CI das imagens

O workflow `.github/workflows/docker.yml` valida, a cada push/PR, que as imagens
de produção do backend e do frontend compilam. Para publicar num registry
(GHCR, Docker Hub…), descomente as etapas de push e configure os secrets do
repositório — a base já está pronta.

---

## Checklist de produção

- [ ] `ENVIRONMENT=production` e `SECRET_KEY`/`CONNECTOR_SECRET_KEY` fortes
- [ ] `CORS_ALLOWED_ORIGINS`, `PUBLIC_BASE_URL` e `APP_BASE_URL` com a URL pública real
- [ ] `REQUIRE_EMAIL_VERIFICATION=true` + `EMAIL_PROVIDER=resend` (envio real dos links)
- [ ] HTTPS na frente (proxy TLS)
- [ ] Backup automático do MongoDB
- [ ] `PLATFORM_ADMIN_EMAILS` com o seu e-mail (para o painel admin)
- [ ] Credenciais das integrações OAuth (quando for ligá-las)
