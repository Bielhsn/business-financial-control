from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class VerifyEmailRequest(BaseModel):
    # Aceita o token longo do link (fluxo logado é legado; o principal é público).
    code: str = Field(min_length=4, max_length=200)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    # Token longo vindo do link do e-mail (não é mais um código de 6 dígitos).
    token: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=128)


class ConfirmEmailRequest(BaseModel):
    """Confirmação pública de e-mail pelo link (a pessoa ainda não está logada)."""

    email: EmailStr
    token: str = Field(min_length=1, max_length=200)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(min_length=1)


class MessageResponse(BaseModel):
    message: str
