import httpx
import pytest

from app.core.exceptions import ConnectorError
from app.infrastructure.connectors.hotmart import HotmartConnector

pytestmark = pytest.mark.anyio

_TOKEN_URL = "https://token.test/oauth/token"
_SALES_URL = "https://api.test/sales/history"

_SALE_ITEM = {
    "purchase": {
        "transaction": "HP1234567890",
        "status": "APPROVED",
        "approved_date": 1_780_000_000_000,
        "price": {"value": 197.0, "currency_code": "BRL"},
    },
    "product": {"name": "Curso de Python"},
    "buyer": {"name": "Maria Silva", "email": "maria@example.com"},
}

_REFUND_ITEM = {
    "purchase": {
        "transaction": "HP0000000001",
        "status": "REFUNDED",
        "approved_date": 1_780_000_500_000,
        "price": {"value": 97.0},
    },
    "product": {"name": "Curso de SQL"},
    "buyer": {"name": "João", "email": "joao@example.com"},
}

_PENDING_ITEM = {
    "purchase": {"transaction": "HP9", "status": "STARTED", "price": {"value": 10.0}},
    "product": {"name": "X"},
    "buyer": {},
}


def _make_connector(handler: object) -> HotmartConnector:
    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]
    return HotmartConnector(token_url=_TOKEN_URL, sales_url=_SALES_URL, transport=transport)


async def test_fetch_sales_maps_and_filters_statuses() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/oauth/token"):
            return httpx.Response(200, json={"access_token": "tok-123"})
        assert request.headers["Authorization"] == "Bearer tok-123"
        return httpx.Response(
            200, json={"items": [_SALE_ITEM, _REFUND_ITEM, _PENDING_ITEM], "page_info": {}}
        )

    sales = await _make_connector(handler).fetch_sales(
        {"client_id": "cid", "client_secret": "sec"}, since=None
    )

    # PENDING é ignorado; APPROVED e REFUNDED viram vendas normalizadas.
    assert len(sales) == 2
    sale = next(s for s in sales if s.external_id == "HP1234567890")
    assert sale.amount_cents == 19700
    assert sale.is_refund is False
    assert sale.description == "Curso de Python"
    assert sale.buyer_email == "maria@example.com"
    refund = next(s for s in sales if s.external_id == "HP0000000001")
    assert refund.is_refund is True
    assert refund.amount_cents == 9700


async def test_fetch_sales_follows_pagination() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/oauth/token"):
            return httpx.Response(200, json={"access_token": "tok"})
        if request.url.params.get("page_token") == "p2":
            return httpx.Response(200, json={"items": [_REFUND_ITEM], "page_info": {}})
        return httpx.Response(
            200, json={"items": [_SALE_ITEM], "page_info": {"next_page_token": "p2"}}
        )

    sales = await _make_connector(handler).fetch_sales(
        {"client_id": "c", "client_secret": "s"}, since=None
    )
    assert {s.external_id for s in sales} == {"HP1234567890", "HP0000000001"}


async def test_invalid_credentials_raise_connector_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid_client"})

    with pytest.raises(ConnectorError, match="inválidas"):
        await _make_connector(handler).test_connection({"client_id": "x", "client_secret": "y"})


async def test_missing_credentials_raise_before_request() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("não deveria chamar a rede")

    with pytest.raises(ConnectorError, match="client_id"):
        await _make_connector(handler).test_connection({"client_id": "", "client_secret": ""})
