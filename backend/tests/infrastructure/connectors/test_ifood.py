from datetime import UTC, datetime

import httpx
import pytest

from app.core.exceptions import ConnectorError
from app.infrastructure.connectors.ifood import IFoodConnector

pytestmark = pytest.mark.anyio

_BASE = "https://ifood.test"

_SALE = {
    "orderId": "order-abc-123",
    "orderIdShort": "1234",
    "type": "SALE",
    "date": "2026-07-01T12:30:00Z",
    "bundle": {"total": {"value": 45.90}},
    "customer": {"name": "Maria Silva"},
    "items": [{"name": "X-Burger"}, {"name": "Batata"}],
}

_CANCELLATION = {
    "orderId": "order-def-456",
    "orderIdShort": "5678",
    "type": "CANCELLATION",
    "date": "2026-07-02",
    "bundle": {"total": {"value": 30.00}},
    "customer": {"name": "João"},
}

_ZERO = {"orderId": "order-zero", "type": "SALE", "bundle": {"total": {"value": 0}}}


def _make_connector(handler: object) -> IFoodConnector:
    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]
    return IFoodConnector(base_url=_BASE, transport=transport)


async def test_fetch_sales_maps_orders_and_cancellations() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer tok-123"
        if request.url.path.endswith("/merchants"):
            return httpx.Response(200, json=[{"id": "merchant-1", "name": "Lanchonete"}])
        return httpx.Response(200, json={"sales": [_SALE, _CANCELLATION, _ZERO]})

    sales = await _make_connector(handler).fetch_sales({"access_token": "tok-123"}, since=None)

    # O registro de valor zero é ignorado; venda e cancelamento são mapeados.
    assert len(sales) == 2
    sale = next(s for s in sales if s.external_id == "order-abc-123")
    assert sale.amount_cents == 4590
    assert sale.is_refund is False
    assert sale.description == "X-Burger, Batata"
    assert sale.buyer_name == "Maria Silva"
    assert sale.occurred_at == datetime(2026, 7, 1, 12, 30, tzinfo=UTC)

    cancellation = next(s for s in sales if s.external_id == "order-def-456")
    assert cancellation.is_refund is True
    assert cancellation.amount_cents == 3000
    assert cancellation.description == "Pedido iFood #5678"


async def test_fetch_sales_uses_stored_merchant_id_and_paginates() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        # merchant_id guardado → não consulta a lista de lojas.
        assert not request.url.path.endswith("/merchants")
        assert "merchant-fixo" in request.url.path
        page = int(request.url.params["page"])
        calls.append(page)
        if page == 1:
            return httpx.Response(
                200, json={"sales": [dict(_SALE, orderId=f"o{n}") for n in range(100)]}
            )
        return httpx.Response(200, json={"sales": [dict(_SALE, orderId="last")]})

    sales = await _make_connector(handler).fetch_sales(
        {"access_token": "tok", "merchant_id": "merchant-fixo"}, since=None
    )

    # Página cheia (100) força buscar a próxima; a segunda (1 item) encerra.
    assert calls == [1, 2]
    assert any(s.external_id == "last" for s in sales)


async def test_missing_access_token_raises_before_request() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("não deveria chamar a rede")

    with pytest.raises(ConnectorError, match="Reconecte"):
        await _make_connector(handler).fetch_sales({}, since=None)


async def test_rejected_token_raises_connector_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    with pytest.raises(ConnectorError, match="recusou o acesso"):
        await _make_connector(handler).test_connection({"access_token": "expired"})


async def test_since_filter_is_sent_as_begin_local_date() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/merchants"):
            return httpx.Response(200, json=[{"id": "m1"}])
        seen["begin"] = request.url.params.get("beginLocalDate", "")
        return httpx.Response(200, json={"sales": []})

    since = datetime(2026, 6, 15, 9, 0, tzinfo=UTC)
    await _make_connector(handler).fetch_sales({"access_token": "t"}, since=since)
    assert seen["begin"] == "2026-06-15"
