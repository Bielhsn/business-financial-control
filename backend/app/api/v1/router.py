from fastapi import APIRouter

from app.api.v1.routers import (
    admin,
    advisor,
    analytics,
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
    oauth_callback,
    plans,
    subscription,
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
api_router.include_router(oauth_callback.router)
api_router.include_router(cnpj.router)
api_router.include_router(invitations.router)
api_router.include_router(plans.router)
api_router.include_router(subscription.router)
api_router.include_router(admin.router)
api_router.include_router(analytics.router)
