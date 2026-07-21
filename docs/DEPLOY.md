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
`ANTHROPIC_API_KEY` (IA), `GOOGLE_CLIENT_ID` (login Google), `EMAIL_*`/`SMTP_*`
(e-mails reais), `*_CLIENT_ID`/`*_CLIENT_SECRET` (integrações OAuth).

> **Nunca** faça commit do `backend/.env` — ele já está no `.gitignore`.

## 3. Subir a stack

```bash
docker compose -f infra/docker-compose.prod.yml up -d --build
```

- O frontend fica em `http://SEU_SERVIDOR/`.
- Verifique a saúde da API: `http://SEU_SERVIDOR/api/v1/health` → `{"status":"ok","database":"ok"}`.
- Logs: `docker compose -f infra/docker-compose.prod.yml logs -f backend`.

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
