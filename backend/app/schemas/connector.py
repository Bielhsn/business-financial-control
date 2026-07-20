from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.connector.entities import ConnectionStatus


class CredentialFieldResponse(BaseModel):
    key: str
    label: str
    secret: bool
    help_text: str | None


class ConnectorDefinitionResponse(BaseModel):
    provider: str
    name: str
    group: str
    description: str
    credential_fields: list[CredentialFieldResponse]
    capabilities: list[str]
    auth_type: str = "credentials"


class AvailableConnectorsResponse(BaseModel):
    connectors: list[ConnectorDefinitionResponse]


class ConnectRequest(BaseModel):
    provider: str = Field(min_length=1, max_length=50)
    # Campos livres conforme o provedor (validados contra o registro na aplicação).
    credentials: dict[str, str]


class ConnectionResponse(BaseModel):
    id: str
    company_id: str
    provider: str
    status: ConnectionStatus
    config: dict[str, str]
    last_synced_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class SyncResultResponse(BaseModel):
    provider: str
    imported: int
    skipped: int
    details: dict[str, int]


class OAuthAuthorizeResponse(BaseModel):
    authorize_url: str
