from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.v1.deps import (
    get_current_user,
    get_password_hasher,
    get_refresh_token_repository,
    get_token_service,
    get_user_repository,
)
from app.application.auth.authenticate_user import AuthenticateUserUseCase
from app.application.auth.logout_user import LogoutUseCase
from app.application.auth.refresh_access_token import RefreshAccessTokenUseCase
from app.application.auth.register_user import RegisterUserUseCase
from app.core.config import Settings, get_settings
from app.core.rate_limit import limiter
from app.domain.auth.ports import PasswordHasher, TokenService
from app.domain.auth.repository import RefreshTokenRepository
from app.domain.user.entities import User
from app.domain.user.repository import UserRepository
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    payload: RegisterRequest,
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
) -> User:
    use_case = RegisterUserUseCase(user_repository, password_hasher)
    return await use_case.execute(
        email=payload.email, password=payload.password, full_name=payload.full_name
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    refresh_token_repository: Annotated[
        RefreshTokenRepository, Depends(get_refresh_token_repository)
    ],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    use_case = AuthenticateUserUseCase(
        user_repository, refresh_token_repository, password_hasher, token_service, settings
    )
    token_pair = await use_case.execute(email=payload.email, password=payload.password)
    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh(
    request: Request,
    payload: RefreshRequest,
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    refresh_token_repository: Annotated[
        RefreshTokenRepository, Depends(get_refresh_token_repository)
    ],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    use_case = RefreshAccessTokenUseCase(
        user_repository, refresh_token_repository, token_service, settings
    )
    token_pair = await use_case.execute(raw_refresh_token=payload.refresh_token)
    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshRequest,
    refresh_token_repository: Annotated[
        RefreshTokenRepository, Depends(get_refresh_token_repository)
    ],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> None:
    use_case = LogoutUseCase(refresh_token_repository, token_service)
    await use_case.execute(raw_refresh_token=payload.refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user
