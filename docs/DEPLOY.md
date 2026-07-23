# Deploy — Aurum OS

Guia para colocar o Aurum OS em produção com Docker. A stack é composta por
quatro serviços: **frontend** (nginx servindo o SPA), **backend** (FastAPI),
**MongoDB** e **Redis**.

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

`MONGODB_URI` e `REDIS_URL` **não** precisam ser definidos no `.env` — o
`docker-compose.prod.yml` já os aponta para os serviços internos.

Opcionais (habilitam funcionalidades): `PLATFORM_ADMIN_EMAILS` (painel admin),
`ANTHROPIC_API_KEY` (IA), `GOOGLE_CLIENT_ID` (login Google),
`EMAIL_PROVIDER=resend` + `RESEND_API_KEY` + `EMAIL_FROM` (e-mails reais de
verificação de conta e reset de senha), `*_CLIENT_ID`/`*_CLIENT_SECRET`
(integrações OAuth).

> **E-mails em produção:** por padrão `EMAIL_PROVIDER=console` só imprime o
> código no log (dev). Para enviar de verdade, crie uma conta no
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
- [ ] `CORS_ALLOWED_ORIGINS` e `PUBLIC_BASE_URL` com a URL pública real
- [ ] HTTPS na frente (proxy TLS)
- [ ] Backup automático do MongoDB
- [ ] `PLATFORM_ADMIN_EMAILS` com o seu e-mail (para o painel admin)
- [ ] Credenciais das integrações OAuth (quando for ligá-las)
