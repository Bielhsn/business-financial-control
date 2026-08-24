from pydantic import BaseModel, EmailStr, Field, model_validator


class RegisterRequest(BaseModel):
    """Cadastro: cria a conta do responsável e a primeira empresa junto.

    Antes eram dois passos desconectados — a conta nascia sem empresa, e quem
    abandonasse o onboarding ficava com um login que não levava a lugar nenhum.
    O restante do perfil (segmento, porte, cidade) continua no onboarding, que é
    onde a personalização por segmento já funciona.
    """

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    password_confirmation: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)
    company_name: str = Field(min_length=1, max_length=200)
    # Obrigatório no cadastro novo. Empresas criadas antes seguem válidas sem
    # ele — exigir retroativamente deixaria contas em uso num estado que o
    # próprio sistema não permite mais criar.
    cnpj: str = Field(min_length=11, max_length=20)
    # Telefone: canal de contato para suporte e recuperação de conta.
    phone: str | None = Field(default=None, max_length=40)
    # Cargo: calibra a linguagem do produto e o contexto que a IA recebe.
    job_role: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def _passwords_must_match(self) -> "RegisterRequest":
        # Comparação também no servidor: a do frontend é conveniência, não
        # garantia — qualquer cliente pode enviar o par divergente direto na API
        # e cadastrar uma senha que a pessoa não sabe qual é.
        if self.password != self.password_confirmation:
            raise ValueError("As senhas não conferem.")
        return self


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
