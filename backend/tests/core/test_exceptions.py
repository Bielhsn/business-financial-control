from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
    register_exception_handlers,
)


def test_error_subclasses_carry_the_expected_status_code() -> None:
    assert NotFoundError().status_code == 404
    assert ValidationError().status_code == 422
    assert UnauthorizedError().status_code == 401
    assert ForbiddenError().status_code == 403
    assert ConflictError().status_code == 409


def _build_test_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom/app-error")
    async def raise_app_error() -> None:
        raise NotFoundError("Empresa não encontrada", details={"company_id": "123"})

    @app.get("/boom/unhandled")
    async def raise_unhandled() -> None:
        raise RuntimeError("algo quebrou")

    @app.get("/boom/validation")
    async def raise_validation(value: int) -> dict[str, int]:
        return {"value": value}

    return app


def test_app_error_is_converted_to_consistent_json_response() -> None:
    client = TestClient(_build_test_app(), raise_server_exceptions=False)

    response = client.get("/boom/app-error")

    assert response.status_code == 404
    assert response.json() == {
        "error": "NotFoundError",
        "message": "Empresa não encontrada",
        "details": {"company_id": "123"},
    }


def test_unhandled_exception_is_converted_to_generic_500_response() -> None:
    client = TestClient(_build_test_app(), raise_server_exceptions=False)

    response = client.get("/boom/unhandled")

    assert response.status_code == 500
    assert response.json() == {
        "error": "InternalServerError",
        "message": "Erro interno do servidor",
        "details": {},
    }


def test_app_error_is_an_exception() -> None:
    assert isinstance(NotFoundError(), AppError)
    assert isinstance(NotFoundError(), Exception)


def test_request_validation_error_is_converted_to_consistent_json_response() -> None:
    client = TestClient(_build_test_app())

    response = client.get("/boom/validation", params={"value": "not-an-int"})

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "ValidationError"
    assert body["message"] == "Dados inválidos"
    assert "errors" in body["details"]
