from fastapi.testclient import TestClient

from app.main import app


def test_security_headers_are_present_on_responses() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["content-security-policy"] == (
        "default-src 'none'; frame-ancestors 'none'"
    )
    assert "camera=()" in response.headers["permissions-policy"]
    # HSTS só em produção — os testes rodam em development.
    assert "strict-transport-security" not in response.headers


def test_cors_allows_configured_origin_and_blocks_others() -> None:
    client = TestClient(app)

    allowed = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"

    blocked = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    # Origem fora da lista: preflight recusado (sem headers de allow).
    assert "access-control-allow-origin" not in blocked.headers
