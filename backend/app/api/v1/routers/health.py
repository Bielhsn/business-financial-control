from fastapi import APIRouter

from app.infrastructure.database.mongodb import ping_database

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    database_status = "ok" if await ping_database() else "unavailable"
    return {"status": "ok", "database": database_status}
