from fastapi import APIRouter

from app.api.v1.routers import (
    auth,
    blueprint,
    catalog,
    clients,
    companies,
    employees,
    financial,
    health,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(companies.router)
api_router.include_router(blueprint.router)
api_router.include_router(financial.router)
api_router.include_router(clients.router)
api_router.include_router(catalog.router)
api_router.include_router(employees.router)
