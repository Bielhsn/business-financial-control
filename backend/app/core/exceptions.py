from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

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

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="InternalServerError", message="Erro interno do servidor"
            ).model_dump(),
        )
