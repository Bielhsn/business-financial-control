"""Blocos de domínio para integrações via OAuth2 (authorization-code).

Tudo aqui é puro (sem I/O): a configuração por provedor, os tokens normalizados
e o "state" assinado que carrega o contexto (empresa/usuário/provedor) com
segurança entre o redirect de ida e o callback de volta. O cliente HTTP que
troca o código por tokens vive na camada de infraestrutura.
"""

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from app.core.exceptions import ValidationError


@dataclass(frozen=True)
class OAuthConfig:
    """Metadados OAuth de um provedor. client_id/secret NÃO ficam aqui — vêm de
    variáveis de ambiente (o dono da plataforma registra o app parceiro)."""

    authorize_url: str
    token_url: str
    scopes: tuple[str, ...]
    client_id_env: str
    client_secret_env: str


@dataclass(frozen=True)
class OAuthTokens:
    access_token: str
    refresh_token: str | None
    expires_at: datetime | None
    scope: str | None = None

    def is_expired(self, *, now: datetime | None = None, leeway_seconds: int = 60) -> bool:
        if self.expires_at is None:
            return False
        moment = now or datetime.now(UTC)
        return self.expires_at <= moment + timedelta(seconds=leeway_seconds)


class OAuthProvider(Protocol):
    """Conector OAuth: além de buscar vendas, sabe fazer a dança do OAuth2."""

    provider: str

    def build_authorize_url(self, *, redirect_uri: str, state: str) -> str: ...

    async def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthTokens: ...

    async def refresh(self, *, refresh_token: str) -> OAuthTokens: ...


# --- State assinado (CSRF + portador de contexto) ---

_STATE_TTL_SECONDS = 600  # 10 min entre iniciar e concluir o OAuth


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def build_oauth_state(
    *,
    secret_key: str,
    company_id: str,
    user_id: str,
    provider: str,
    params: dict[str, str] | None = None,
    now: datetime | None = None,
) -> str:
    """Cria um state opaco e assinado (HMAC-SHA256). Funciona como token CSRF e
    também carrega com segurança quem/qual empresa iniciou o fluxo, além de
    parâmetros por provedor (ex.: shop do Shopify) que precisam voltar no callback."""
    issued = now or datetime.now(UTC)
    payload = {
        "cid": company_id,
        "uid": user_id,
        "prov": provider,
        "params": params or {},
        "nonce": secrets.token_urlsafe(8),
        "exp": int((issued + timedelta(seconds=_STATE_TTL_SECONDS)).timestamp()),
    }
    body = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(secret_key.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    return f"{body}.{_b64url_encode(signature)}"


@dataclass(frozen=True)
class OAuthStatePayload:
    company_id: str
    user_id: str
    provider: str
    params: dict[str, str]


def parse_oauth_state(
    state: str, *, secret_key: str, now: datetime | None = None
) -> OAuthStatePayload:
    """Valida a assinatura e a expiração do state, devolvendo o contexto. Levanta
    ValidationError se for adulterado ou expirado."""
    try:
        body, signature = state.split(".", 1)
    except ValueError as exc:
        raise ValidationError("State de OAuth inválido.") from exc

    expected = hmac.new(secret_key.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    if not hmac.compare_digest(_b64url_encode(expected), signature):
        raise ValidationError("Assinatura do state de OAuth inválida.")

    try:
        payload = json.loads(_b64url_decode(body))
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValidationError("State de OAuth corrompido.") from exc

    moment = now or datetime.now(UTC)
    if int(payload.get("exp", 0)) < int(moment.timestamp()):
        raise ValidationError("O fluxo de OAuth expirou. Tente conectar novamente.")

    return OAuthStatePayload(
        company_id=payload["cid"],
        user_id=payload["uid"],
        provider=payload["prov"],
        params=payload.get("params", {}),
    )
