from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.v1.deps import get_cnpj_lookup
from app.core.exceptions import ValidationError
from app.core.rate_limit import limiter
from app.domain.company.cnpj import is_valid_cnpj, normalize_cnpj
from app.domain.company.cnpj_lookup import CnpjLookup
from app.schemas.cnpj import CnpjLookupResponse

router = APIRouter(prefix="/cnpj", tags=["cnpj"])


# Público de propósito: o formulário de cadastro precisa confirmar a empresa
# ANTES de existir conta para autenticar. Os dados são públicos na Receita e a
# BrasilAPI já os serve sem chave — o risco não é vazamento, é virar proxy de
# raspagem. Daí o limite por minuto, mais apertado que o dos demais endpoints.
@router.get("/{cnpj}", response_model=CnpjLookupResponse)
@limiter.limit("10/minute")
async def lookup_cnpj(
    request: Request,
    cnpj: str,
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
