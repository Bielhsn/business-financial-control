from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.v1.deps import (
    get_current_user,
    get_email_sender,
    get_google_verifier,
    get_password_hasher,
    get_refresh_token_repository,
    get_token_service,
    get_user_repository,
    get_verification_code_repository,
)
from app.application.auth.authenticate_user import AuthenticateUserUseCase
from app.application.auth.change_password import ChangePasswordUseCase
from app.application.auth.email_verification import (
    RequestEmailVerificationUseCase,
    VerifyEmailUseCase,
)
from app.application.auth.google_login import LoginWithGoogleUseCase
from app.application.auth.logout_user import LogoutUseCase
from app.application.auth.password_recovery import (
    RequestPasswordResetUseCase,
    ResetPasswordUseCase,
)
from app.application.auth.refresh_access_token import RefreshAccessTokenUseCase
from app.application.auth.register_user import RegisterUserUseCase
from app.core.audit import audit_event
from app.core.config import Settings, get_settings
from app.core.exceptions import UnauthorizedError
from app.core.rate_limit import limiter
from app.domain.auth.google import GoogleTokenVerifier
from app.domain.auth.ports import PasswordHasher, TokenService
from app.domain.auth.repository import RefreshTokenRepository
from app.domain.auth.verification import VerificationCodeRepository
from app.domain.notifications.email import EmailSender
from app.domain.user.entities import User
from app.domain.user.repository import UserRepository
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    GoogleLoginRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    payload: RegisterRequest,
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    code_repository: Annotated[
        VerificationCodeRepository, Depends(get_verification_code_repository)
    ],
    email_sender: Annotated[EmailSender, Depends(get_email_sender)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    use_case = RegisterUserUseCase(user_repository, password_hasher, settings)
    user = await use_case.execute(
        email=payload.email, password=payload.password, full_name=payload.full_name
    )
    audit_event("user_registered", user_id=user.id)
    # Se a verificação por e-mail está ligada, já dispara o código de confirmação.
    if settings.require_email_verification:
        await RequestEmailVerificationUseCase(
            user_repository, code_repository, email_sender, settings
        ).execute(user_id=user.id)
    return user


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def verify_email(
    request: Request,
    payload: VerifyEmailRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    code_repository: Annotated[
        VerificationCodeRepository, Depends(get_verification_code_repository)
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    await VerifyEmailUseCase(user_repository, code_repository, settings).execute(
        user_id=current_user.id, code=payload.code
    )
    audit_event("email_verified", user_id=current_user.id)


@router.post("/request-verification", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("3/minute")
async def request_verification(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    code_repository: Annotated[
        VerificationCodeRepository, Depends(get_verification_code_repository)
    ],
    email_sender: Annotated[EmailSender, Depends(get_email_sender)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    await RequestEmailVerificationUseCase(
        user_repository, code_repository, email_sender, settings
    ).execute(user_id=current_user.id)


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    code_repository: Annotated[
        VerificationCodeRepository, Depends(get_verification_code_repository)
    ],
    email_sender: Annotated[EmailSender, Depends(get_email_sender)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> MessageResponse:
    await RequestPasswordResetUseCase(
        user_repository, code_repository, email_sender, settings
    ).execute(email=payload.email)
    # Resposta idêntica exista ou não a conta (não vaza se o e-mail está cadastrado).
    return MessageResponse(
        message="Se houver uma conta com este e-mail, enviamos um código de redefinição."
    )


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    code_repository: Annotated[
        VerificationCodeRepository, Depends(get_verification_code_repository)
    ],
    refresh_token_repository: Annotated[
        RefreshTokenRepository, Depends(get_refresh_token_repository)
    ],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    await ResetPasswordUseCase(
        user_repository,
        code_repository,
        refresh_token_repository,
        password_hasher,
        settings,
    ).execute(email=payload.email, code=payload.code, new_password=payload.new_password)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    refresh_token_repository: Annotated[
        RefreshTokenRepository, Depends(get_refresh_token_repository)
    ],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
) -> None:
    await ChangePasswordUseCase(user_repository, refresh_token_repository, password_hasher).execute(
        user_id=current_user.id,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    audit_event("password_changed", user_id=current_user.id)


@router.post("/google", response_model=TokenResponse)
@limiter.limit("10/minute")
async def google_login(
    request: Request,
    payload: GoogleLoginRequest,
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    refresh_token_repository: Annotated[
        RefreshTokenRepository, Depends(get_refresh_token_repository)
    ],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    google_verifier: Annotated[GoogleTokenVerifier, Depends(get_google_verifier)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    use_case = LoginWithGoogleUseCase(
        user_repository,
        refresh_token_repository,
        password_hasher,
        token_service,
        google_verifier,
        settings,
    )
    token_pair = await use_case.execute(id_token=payload.id_token)
    audit_event("login_google_succeeded")
    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
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
    try:
        token_pair = await use_case.execute(email=payload.email, password=payload.password)
    except UnauthorizedError:
        # Auditar falhas de login permite detectar tentativas de força bruta.
        # Não registra a senha nem revela se o e-mail existe.
        audit_event("login_failed", email=payload.email)
        raise
    user = await user_repository.get_by_email(payload.email)
    audit_event("login_succeeded", user_id=user.id if user else None)
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
