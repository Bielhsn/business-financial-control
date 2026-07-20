from fastapi import APIRouter

from app.api.v1.routers import (
    advisor,
    appointment,
    audit,
    auth,
    blueprint,
    catalog,
    clients,
    cnpj,
    companies,
    connectors,
    dashboard,
    employees,
    financial,
    health,
    insights,
    invitations,
    notifications,
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
api_router.include_router(dashboard.router)
api_router.include_router(insights.router)
api_router.include_router(audit.router)
api_router.include_router(notifications.router)
api_router.include_router(advisor.router)
api_router.include_router(appointment.router)
api_router.include_router(connectors.router)
api_router.include_router(cnpj.router)
api_router.include_router(invitations.router)
