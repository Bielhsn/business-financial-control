from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.observability import configure_error_tracking
from app.core.rate_limit import limiter
from app.core.security_headers import SecurityHeadersMiddleware
from app.infrastructure.database.mongodb import close_mongo_connection, connect_to_mongo

settings = get_settings()
configure_logging(log_level=settings.log_level, environment=settings.environment)
# Antes de criar o app: falha de inicialização também precisa ser reportada.
configure_error_tracking(settings)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await connect_to_mongo()
    logger.info("application_startup")
    yield
    await close_mongo_connection()
    logger.info("application_shutdown")


app = FastAPI(
    title="Business Financial Control API",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# CORS restrito às origens configuradas (frontend). Sem cookies de sessão —
# autenticação vai no header Authorization — então allow_credentials fica False.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(SecurityHeadersMiddleware, enable_hsts=settings.environment == "production")

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)


# HEAD junto de GET: balanceadores e monitores de uptime (o health check da
# Render entre eles) sondam com HEAD, e o `@app.get` do FastAPI — ao contrário
# de uma rota Starlette pura — não registra HEAD sozinho. Sem isso a sonda leva
# 405 e enche o log de "Method Not Allowed" num serviço que está saudável.
@app.api_route("/", methods=["GET", "HEAD"])
async def root() -> dict[str, str]:
    return {"name": "business-financial-control-api", "status": "ok"}
