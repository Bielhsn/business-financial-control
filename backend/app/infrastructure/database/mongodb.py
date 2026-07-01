from typing import Any

from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.core.config import get_settings
from app.core.logging import get_logger
from app.infrastructure.database.models.company import CompanyDocument
from app.infrastructure.database.models.company_blueprint import CompanyBlueprintDocument
from app.infrastructure.database.models.company_membership import CompanyMembershipDocument
from app.infrastructure.database.models.financial_category import FinancialCategoryDocument
from app.infrastructure.database.models.financial_transaction import (
    FinancialTransactionDocument,
)
from app.infrastructure.database.models.refresh_token import RefreshTokenDocument
from app.infrastructure.database.models.user import UserDocument

logger = get_logger(__name__)

_client: AsyncMongoClient[dict[str, Any]] | None = None


def get_client() -> AsyncMongoClient[dict[str, Any]]:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncMongoClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=settings.mongodb_server_selection_timeout_ms,
            # datetimes lidos do Mongo vêm com tzinfo (UTC), evitando comparações
            # entre naive e aware que causariam bugs em validações de expiração.
            tz_aware=True,
        )
    return _client


async def connect_to_mongo() -> None:
    settings = get_settings()
    client = get_client()
    await init_beanie(
        database=client[settings.mongodb_db_name],
        document_models=[
            UserDocument,
            RefreshTokenDocument,
            CompanyDocument,
            CompanyMembershipDocument,
            CompanyBlueprintDocument,
            FinancialCategoryDocument,
            FinancialTransactionDocument,
        ],
    )
    logger.info("mongodb_connected", database=settings.mongodb_db_name)


async def close_mongo_connection() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
        logger.info("mongodb_connection_closed")


async def ping_database() -> bool:
    client = get_client()
    try:
        await client.admin.command("ping")
        return True
    except Exception:
        logger.warning("mongodb_ping_failed")
        return False
