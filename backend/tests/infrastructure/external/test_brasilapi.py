import httpx
import pytest

from app.core.exceptions import ConnectorError, NotFoundError
from app.infrastructure.external.brasilapi import BrasilApiCnpjLookup

pytestmark = pytest.mark.anyio

_BASE = "https://brasil.test/api/cnpj/v1"


def _lookup(handler: object) -> BrasilApiCnpjLookup:
    return BrasilApiCnpjLookup(base_url=_BASE, transport=httpx.MockTransport(handler))  # type: ignore[arg-type]


async def test_fetch_maps_active_company() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/11222333000181")
        return httpx.Response(
            200,
            json={
                "razao_social": "Empresa Exemplo LTDA",
                "nome_fantasia": "Exemplo",
                "descricao_situacao_cadastral": "ATIVA",
                "municipio": "SAO PAULO",
                "uf": "SP",
                "email": "contato@exemplo.com",
                "ddd_telefone_1": "1133224455",
                "cnae_fiscal_descricao": "Desenvolvimento de software",
            },
        )

    info = await _lookup(handler).fetch("11222333000181")

    assert info.legal_name == "Empresa Exemplo LTDA"
    assert info.trade_name == "Exemplo"
    assert info.is_active is True
    assert info.state == "SP"
    assert info.main_activity == "Desenvolvimento de software"


async def test_inactive_company_flagged() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"razao_social": "X", "descricao_situacao_cadastral": "BAIXADA"}
        )

    info = await _lookup(handler).fetch("11222333000181")
    assert info.is_active is False
    assert info.status == "BAIXADA"


async def test_not_found_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "CNPJ não encontrado"})

    with pytest.raises(NotFoundError):
        await _lookup(handler).fetch("11222333000181")


async def test_upstream_error_raises_connector_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={})

    with pytest.raises(ConnectorError):
        await _lookup(handler).fetch("11222333000181")
