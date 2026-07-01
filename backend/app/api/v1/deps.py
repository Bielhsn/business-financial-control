from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.exceptions import UnauthorizedError
from app.domain.auth.ports import PasswordHasher, TokenService
from app.domain.auth.repository import RefreshTokenRepository
from app.domain.user.entities import User
from app.domain.user.repository import UserRepository
from app.infrastructure.repositories.refresh_token_repository import (
    BeanieRefreshTokenRepository,
)
from app.infrastructure.repositories.user_repository import BeanieUserRepository
from app.infrastructure.security.password import Argon2PasswordHasher
from app.infrastructure.security.tokens import JWTTokenService

_password_hasher = Argon2PasswordHasher()
# auto_error=False: preferimos levantar UnauthorizedError (401) nós mesmos, em vez do
# 403 que o HTTPBearer retorna por padrão quando o header Authorization está ausente.
_bearer_scheme = HTTPBearer(auto_error=False)


def get_user_repository() -> UserRepository:
    return BeanieUserRepository()


def get_refresh_token_repository() -> RefreshTokenRepository:
    return BeanieRefreshTokenRepository()


def get_password_hasher() -> PasswordHasher:
    return _password_hasher


def get_token_service(settings: Annotated[Settings, Depends(get_settings)]) -> TokenService:
    return JWTTokenService(settings)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> User:
    if credentials is None:
        raise UnauthorizedError("Credenciais não fornecidas.")

    payload = token_service.decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise UnauthorizedError("Token inválido.")

    user = await user_repository.get_by_id(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Usuário inválido ou inativo.")
    return user
