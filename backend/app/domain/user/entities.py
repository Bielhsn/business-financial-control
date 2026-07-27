from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: str
    email: str
    hashed_password: str
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # E-mail confirmado. Default True para não invalidar contas já existentes; o
    # registro cria como False quando require_email_verification está ligado.
    is_verified: bool = True
    # Telefone: canal de contato para suporte e recuperação de conta — o e-mail
    # sozinho trava o atendimento quando a pessoa perde acesso à caixa.
    phone: str | None = None
    # Cargo/função de quem administra a conta. Usado para calibrar a linguagem do
    # produto e o contexto da IA: um dono de barbearia e um contador da mesma
    # empresa precisam de recortes diferentes da mesma informação.
    job_role: str | None = None
