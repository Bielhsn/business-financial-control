from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger
from app.schemas.error import ErrorResponse

logger = get_logger(__name__)


class AppError(Exception):
    """Exceção base de domínio/aplicação, convertida em resposta HTTP consistente."""

    def __init__(
        self, message: str, *, status_code: int = 500, details: dict[str, object] | None = None
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(
        self, message: str = "Recurso não encontrado", details: dict[str, object] | None = None
    ) -> None:
        super().__init__(message, status_code=404, details=details)


class ValidationError(AppError):
    def __init__(
        self, message: str = "Dados inválidos", details: dict[str, object] | None = None
    ) -> None:
        super().__init__(message, status_code=422, details=details)


class UnauthorizedError(AppError):
    def __init__(
        self, message: str = "Não autorizado", details: dict[str, object] | None = None
    ) -> None:
        super().__init__(message, status_code=401, details=details)


class ForbiddenError(AppError):
    def __init__(
        self, message: str = "Acesso negado", details: dict[str, object] | None = None
    ) -> None:
        super().__init__(message, status_code=403, details=details)


class ConflictError(AppError):
    def __init__(
        self, message: str = "Conflito de dados", details: dict[str, object] | None = None
    ) -> None:
        super().__init__(message, status_code=409, details=details)


class AIProviderNotConfiguredError(AppError):
    def __init__(
        self,
        message: str = "Provedor de IA não configurado.",
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message, status_code=503, details=details)


class AIProviderError(AppError):
    def __init__(
        self,
        message: str = "Falha ao gerar sugestões com IA.",
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message, status_code=502, details=details)


class ConnectorError(AppError):
    """Falha ao comunicar com um provedor externo (credenciais inválidas, API
    fora do ar, resposta inesperada). 502: o erro é do provedor, não do cliente."""

    def __init__(
        self,
        message: str = "Falha ao comunicar com o provedor externo.",
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message, status_code=502, details=details)


class ExternalServiceError(AppError):
    """Falha ao usar um serviço externo (ex.: provedor de e-mail). 502: o erro
    vem do serviço, não do cliente."""

    def __init__(
        self,
        message: str = "Falha ao comunicar com um serviço externo.",
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message, status_code=502, details=details)


class PlanLimitError(AppError):
    """Recurso bloqueado pelo plano atual (limite atingido ou funcionalidade não
    incluída). 402 Payment Required: o frontend usa isto para oferecer upgrade."""

    def __init__(
        self,
        message: str = "Seu plano atual não permite esta ação.",
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message, status_code=402, details=details)


def register_exception_handlers(app: FastAPI) -> None:
    """Centraliza a conversão de exceções em respostas HTTP e logs estruturados."""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "app_error",
            error=type(exc).__name__,
            message=exc.message,
            path=request.url.path,
            details=exc.details,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=type(exc).__name__, message=exc.message, details=exc.details
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = jsonable_encoder(exc.errors())
        logger.warning("validation_error", path=request.url.path, errors=errors)
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="ValidationError", message="Dados inválidos", details={"errors": errors}
            ).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Cobre exceções HTTP nativas do Starlette/FastAPI (ex.: 404 de rota inexistente,
        # RateLimitExceeded do slowapi), mantendo o mesmo formato de resposta.
        logger.warning(
            "http_exception",
            status_code=exc.status_code,
            detail=str(exc.detail),
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(error="HTTPException", message=str(exc.detail)).model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="InternalServerError", message="Erro interno do servidor"
            ).model_dump(),
        )
