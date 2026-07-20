from pydantic import BaseModel


class CnpjLookupResponse(BaseModel):
    cnpj: str
    legal_name: str | None
    trade_name: str | None
    status: str | None
    is_active: bool
    city: str | None
    state: str | None
    email: str | None
    phone: str | None
    main_activity: str | None
