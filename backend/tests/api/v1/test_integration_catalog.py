from fastapi.testclient import TestClient

from app.domain.connector.registry import CONNECTOR_PROVIDERS
from tests.registration import register_payload


def _auth_header(client: TestClient, email: str = "dono@example.com") -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json=register_payload(email, "s3cr3t!!", "Dono"),
    )
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "s3cr3t!!"}).json()[
        "access_token"
    ]
    return {"Authorization": f"Bearer {token}"}


def test_catalog_is_the_single_source_of_integrations(client: TestClient) -> None:
    response = client.get("/api/v1/integrations/catalog", headers=_auth_header(client))

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) > 40  # catálogo completo, não só os conectáveis
    assert {"id", "name", "group", "connectable"} <= set(items[0])


def test_connectable_reflects_real_connectors(client: TestClient) -> None:
    items = client.get("/api/v1/integrations/catalog", headers=_auth_header(client)).json()["items"]

    connectable = {item["id"] for item in items if item["connectable"]}
    # "Conectar" só aparece para quem tem conector implementado de verdade.
    assert "hotmart" in connectable
    assert "ifood" in connectable
    assert "rappi" not in connectable
    assert len(connectable) == len(CONNECTOR_PROVIDERS)


def test_catalog_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/integrations/catalog").status_code == 401


def test_catalog_exposes_provider_for_connectable_items(client: TestClient) -> None:
    """`connectable` sem `provider` seria uma promessa vazia: a tela precisa do
    provider para saber qual fluxo abrir. Os dois campos andam juntos."""
    items = client.get("/api/v1/integrations/catalog", headers=_auth_header(client)).json()["items"]

    for item in items:
        if item["connectable"]:
            assert item["provider"], f"{item['id']} diz conectável mas não aponta conector"
        else:
            assert item["provider"] is None


def test_every_connector_provider_is_reachable_from_the_catalog() -> None:
    """Todo conector implementado precisa aparecer no catálogo. Um conector que
    existe e não é listado é trabalho pronto que ninguém consegue usar — foi o
    que aconteceu com a Hotmart."""
    from app.domain.blueprint.integration_registry import INTEGRATION_REGISTRY
    from app.domain.connector.registry import CONNECTOR_PROVIDERS

    no_catalogo = {
        item.connector_provider for item in INTEGRATION_REGISTRY if item.connector_provider
    }

    assert no_catalogo >= CONNECTOR_PROVIDERS
