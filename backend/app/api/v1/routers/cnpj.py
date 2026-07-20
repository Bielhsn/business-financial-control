from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.deps import get_cnpj_lookup, get_current_user
from app.core.exceptions import ValidationError
from app.domain.company.cnpj import is_valid_cnpj, normalize_cnpj
from app.domain.company.cnpj_lookup import CnpjLookup
from app.domain.user.entities import User
from app.schemas.cnpj import CnpjLookupResponse

router = APIRouter(prefix="/cnpj", tags=["cnpj"])


# Não é company-scoped: usado durante a criação da empresa, antes de ela existir.
# Exige apenas usuário autenticado.
@router.get("/{cnpj}", response_model=CnpjLookupResponse)
async def lookup_cnpj(
    cnpj: str,
    current_user: Annotated[User, Depends(get_current_user)],
    cnpj_lookup: Annotated[CnpjLookup, Depends(get_cnpj_lookup)],
) -> CnpjLookupResponse:
    normalized = normalize_cnpj(cnpj)
    # Valida os dígitos localmente antes de gastar uma chamada externa.
    if not is_valid_cnpj(normalized):
        raise ValidationError("CNPJ inválido.")
    info = await cnpj_lookup.fetch(normalized)
    return CnpjLookupResponse(
        cnpj=info.cnpj,
        legal_name=info.legal_name,
        trade_name=info.trade_name,
        status=info.status,
        is_active=info.is_active,
        city=info.city,
        state=info.state,
        email=info.email,
        phone=info.phone,
        main_activity=info.main_activity,
    )
