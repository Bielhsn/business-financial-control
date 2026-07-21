"""Cria (ou promove) a conta de dono/administrador geral da plataforma.

Este script é um utilitário operacional — roda UMA vez contra o banco real para
garantir que exista uma conta de dono já pronta para logar. Ele NÃO expõe nada
pela API e nunca grava a senha em disco.

Uso típico com a stack de produção no ar:

    docker compose -f infra/docker-compose.prod.yml exec \\
        -e ADMIN_PASSWORD='sua-senha-forte' \\
        backend python -m scripts.create_admin --email voce@exemplo.com

Ou localmente (venv ativo e MONGODB_URI apontando para o banco):

    ADMIN_PASSWORD='sua-senha-forte' python -m scripts.create_admin \\
        --email voce@exemplo.com

Comportamento:
- Se a conta não existe, cria já **verificada** (pode logar direto).
- Se já existe, garante que está verificada e ativa; troca a senha se uma for
  informada.
- A senha vem de --password ou da variável de ambiente ADMIN_PASSWORD. Se
  nenhuma for passada, uma senha forte é gerada e mostrada UMA vez no terminal.

Importante: ser "super-admin" da plataforma (painel /admin com MRR, churn, etc.)
depende ADICIONALMENTE de incluir o e-mail em PLATFORM_ADMIN_EMAILS no ambiente
do backend — o script lembra disso ao final, pois é uma configuração, não um
dado no banco.
"""

from __future__ import annotations

import argparse
import asyncio
import secrets
import string
import sys

from app.core.config import get_settings
from app.infrastructure.database.mongodb import (
    close_mongo_connection,
    connect_to_mongo,
)
from app.infrastructure.repositories.user_repository import BeanieUserRepository
from app.infrastructure.security.password import Argon2PasswordHasher

_DEFAULT_NAME = "Administrador"


def _generate_password(length: int = 20) -> str:
    """Gera uma senha forte com letras, dígitos e símbolos seguros para shell."""
    alphabet = string.ascii_letters + string.digits + "!@#$%*-_=+"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cria/promove o dono da plataforma.")
    parser.add_argument("--email", required=True, help="E-mail de login do dono.")
    parser.add_argument(
        "--password",
        default=None,
        help="Senha de login. Se omitida, usa ADMIN_PASSWORD ou gera uma forte.",
    )
    parser.add_argument("--name", default=_DEFAULT_NAME, help="Nome exibido da conta.")
    return parser.parse_args(argv)


async def _run(email: str, password: str, full_name: str) -> None:
    await connect_to_mongo()
    try:
        users = BeanieUserRepository()
        hasher = Argon2PasswordHasher()
        normalized = email.strip().lower()
        hashed = hasher.hash(password)

        existing = await users.get_by_email(normalized)
        if existing is None:
            user = await users.create(
                email=normalized,
                hashed_password=hashed,
                full_name=full_name.strip(),
                is_verified=True,
            )
            action = "criada"
        else:
            updated = await users.update(
                existing.id,
                hashed_password=hashed,
                is_verified=True,
                is_active=True,
            )
            user = updated or existing
            action = "atualizada"
    finally:
        await close_mongo_connection()

    settings = get_settings()
    is_admin = settings.is_platform_admin(normalized)

    print("\n" + "=" * 60)
    print(f"  Conta de dono {action} com sucesso.")
    print("=" * 60)
    print(f"  ID:      {user.id}")
    print(f"  E-mail:  {user.email}")
    print(f"  Senha:   {password}")
    print("  (guarde a senha agora — ela não é gravada em lugar nenhum)")
    print("=" * 60)
    if is_admin:
        print("  Super-admin da plataforma: ATIVO (e-mail está em PLATFORM_ADMIN_EMAILS).")
    else:
        print("  ATENÇÃO: para liberar o painel super-admin (/admin), inclua este")
        print("  e-mail em PLATFORM_ADMIN_EMAILS no ambiente do backend, por ex.:")
        print(f'    PLATFORM_ADMIN_EMAILS="{user.email}"')
        print("  e reinicie o backend.")
    print("=" * 60 + "\n")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    settings = get_settings()
    password = args.password or settings.admin_password or _generate_password()

    asyncio.run(_run(email=args.email, password=password, full_name=args.name))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
