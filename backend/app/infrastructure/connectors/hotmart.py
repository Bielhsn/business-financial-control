import base64
from datetime import UTC, datetime

import httpx

from app.core.exceptions import ConnectorError
from app.domain.connector.entities import NormalizedSale

# URLs oficiais da Hotmart. Parametrizáveis no construtor para os testes usarem
# um transporte mock (httpx.MockTransport) sem tocar a rede.
_DEFAULT_TOKEN_URL = "https://api-sec-vlc.hotmart.com/security/oauth/token"
_DEFAULT_SALES_URL = "https://developers.hotmart.com/payments/api/v1/sales/history"

_APPROVED_STATUSES = {"APPROVED", "COMPLETE", "COMPLETED"}
_REFUND_STATUSES = {"REFUNDED", "CHARGEBACK", "CANCELLED"}
_MAX_PAGES = 50


class HotmartConnector:
    """Conector da Hotmart: autentica via OAuth2 client-credentials e traduz o
    histórico de vendas para `NormalizedSale`."""

    provider = "hotmart"

    def __init__(
        self,
        *,
        token_url: str = _DEFAULT_TOKEN_URL,
        sales_url: str = _DEFAULT_SALES_URL,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._token_url = token_url
        self._sales_url = sales_url
        self._transport = transport

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=30.0, transport=self._transport)

    async def _get_token(self, client: httpx.AsyncClient, credentials: dict[str, str]) -> str:
        client_id = credentials.get("client_id", "")
        client_secret = credentials.get("client_secret", "")
        if not client_id or not client_secret:
            raise ConnectorError("Informe client_id e client_secret da Hotmart.")
        basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        try:
            response = await client.post(
                self._token_url,
                params={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                headers={"Authorization": f"Basic {basic}"},
            )
        except httpx.HTTPError as exc:
            raise ConnectorError("Não foi possível conectar à Hotmart.") from exc
        if response.status_code >= 400:
            raise ConnectorError("Credenciais da Hotmart inválidas ou sem permissão.")
        token = response.json().get("access_token")
        if not isinstance(token, str) or not token:
            raise ConnectorError("A Hotmart não retornou um token de acesso.")
        return token

    async def test_connection(self, credentials: dict[str, str]) -> None:
        async with self._client() as client:
            await self._get_token(client, credentials)

    async def fetch_sales(
        self, credentials: dict[str, str], *, since: datetime | None
    ) -> list[NormalizedSale]:
        async with self._client() as client:
            token = await self._get_token(client, credentials)
            headers = {"Authorization": f"Bearer {token}"}
            params: dict[str, str | int] = {"max_results": 100}
            if since is not None:
                params["start_date"] = int(since.timestamp() * 1000)

            sales: list[NormalizedSale] = []
            for _ in range(_MAX_PAGES):
                try:
                    response = await client.get(self._sales_url, headers=headers, params=params)
                except httpx.HTTPError as exc:
                    raise ConnectorError("Falha ao buscar vendas na Hotmart.") from exc
                if response.status_code >= 400:
                    raise ConnectorError("A Hotmart recusou a consulta de vendas.")
                payload = response.json()
                for item in payload.get("items", []):
                    sale = _parse_sale(item)
                    if sale is not None:
                        sales.append(sale)
                next_token = payload.get("page_info", {}).get("next_page_token")
                if not next_token:
                    break
                params["page_token"] = next_token
            return sales


def _parse_sale(item: dict[str, object]) -> NormalizedSale | None:
    purchase = item.get("purchase") if isinstance(item.get("purchase"), dict) else {}
    buyer = item.get("buyer") if isinstance(item.get("buyer"), dict) else {}
    product = item.get("product") if isinstance(item.get("product"), dict) else {}
    assert isinstance(purchase, dict) and isinstance(buyer, dict) and isinstance(product, dict)

    transaction = purchase.get("transaction")
    if not isinstance(transaction, str) or not transaction:
        return None

    status = str(purchase.get("status", "")).upper()
    if status in _APPROVED_STATUSES:
        is_refund = False
    elif status in _REFUND_STATUSES:
        is_refund = True
    else:
        return None  # PENDING/STARTED etc. não viram lançamento ainda.

    price = purchase.get("price") if isinstance(purchase.get("price"), dict) else {}
    assert isinstance(price, dict)
    value = price.get("value")
    if not isinstance(value, int | float):
        return None
    amount_cents = round(float(value) * 100)
    if amount_cents <= 0:
        return None

    occurred_ms = purchase.get("approved_date") or purchase.get("order_date")
    if isinstance(occurred_ms, int | float):
        occurred_at = datetime.fromtimestamp(float(occurred_ms) / 1000, tz=UTC)
    else:
        occurred_at = datetime.now(UTC)

    product_name = product.get("name") if isinstance(product.get("name"), str) else "Venda Hotmart"
    return NormalizedSale(
        external_id=transaction,
        description=str(product_name),
        amount_cents=amount_cents,
        occurred_at=occurred_at,
        is_refund=is_refund,
        buyer_name=buyer.get("name") if isinstance(buyer.get("name"), str) else None,
        buyer_email=buyer.get("email") if isinstance(buyer.get("email"), str) else None,
    )
