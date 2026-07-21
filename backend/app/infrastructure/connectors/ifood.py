"""Conector do iFood: lê as vendas da loja já autorizada e as traduz para
`NormalizedSale`.

O fluxo de OAuth (o lojista autorizar a própria loja) já é resolvido pelo
framework genérico — este conector cuida do passo seguinte: usar o token de
acesso guardado para buscar as vendas na API do iFood.

Sobre o mapeamento: os nomes dos campos seguem a documentação da API do iFood
(Merchant + Financial). Como o formato exato precisa ser confirmado contra uma
conta real de lojista antes do go-live, todo o parsing fica isolado em funções
puras (`_parse_ifood_sale` e auxiliares), fáceis de ajustar e cobertas por
testes. Assim, no dia em que as credenciais reais existirem, valida-se o formato
e liga-se a sincronização sem tocar no motor de sync, na API ou no frontend.
"""

from datetime import UTC, datetime

import httpx

from app.core.exceptions import ConnectorError
from app.domain.connector.entities import NormalizedSale

# Base da API do iFood. Parametrizável no construtor para os testes usarem um
# transporte mock (httpx.MockTransport) sem tocar a rede.
_DEFAULT_BASE_URL = "https://merchant-api.ifood.com.br"
_MAX_PAGES = 50
_PAGE_SIZE = 100

# `type` do registro financeiro que representa estorno/cancelamento (vira despesa).
_REFUND_TYPES = frozenset(
    {"CANCELLATION", "CANCELLED", "CANCELED", "REFUND", "CHARGEBACK", "DISPUTE"}
)


class IFoodConnector:
    """Conector do iFood: autentica com o token OAuth já autorizado e traduz o
    histórico de vendas para `NormalizedSale`."""

    provider = "ifood"

    def __init__(
        self,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=30.0, transport=self._transport)

    @staticmethod
    def _access_token(credentials: dict[str, str]) -> str:
        token = credentials.get("access_token", "")
        if not token:
            raise ConnectorError("Conexão com o iFood expirada ou incompleta. Reconecte a loja.")
        return token

    async def test_connection(self, credentials: dict[str, str]) -> None:
        token = self._access_token(credentials)
        async with self._client() as client:
            await self._list_merchant_ids(client, token, credentials)

    async def fetch_sales(
        self, credentials: dict[str, str], *, since: datetime | None
    ) -> list[NormalizedSale]:
        token = self._access_token(credentials)
        async with self._client() as client:
            merchant_ids = await self._list_merchant_ids(client, token, credentials)
            sales: list[NormalizedSale] = []
            for merchant_id in merchant_ids:
                sales.extend(await self._fetch_merchant_sales(client, token, merchant_id, since))
            return sales

    async def _list_merchant_ids(
        self, client: httpx.AsyncClient, token: str, credentials: dict[str, str]
    ) -> list[str]:
        # Se a loja já foi guardada na conexão, evita uma chamada extra.
        stored = credentials.get("merchant_id")
        if stored:
            return [stored]

        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = await client.get(
                f"{self._base_url}/merchant/v1.0/merchants", headers=headers
            )
        except httpx.HTTPError as exc:
            raise ConnectorError("Não foi possível conectar ao iFood.") from exc
        if response.status_code >= 400:
            raise ConnectorError(
                "O iFood recusou o acesso à loja (token inválido ou sem permissão)."
            )

        payload = response.json()
        merchants = payload if isinstance(payload, list) else payload.get("merchants", [])
        ids = [
            m["id"]
            for m in merchants
            if isinstance(m, dict) and isinstance(m.get("id"), str) and m["id"]
        ]
        if not ids:
            raise ConnectorError("Nenhuma loja iFood encontrada para esta conta.")
        return ids

    async def _fetch_merchant_sales(
        self,
        client: httpx.AsyncClient,
        token: str,
        merchant_id: str,
        since: datetime | None,
    ) -> list[NormalizedSale]:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self._base_url}/financial/v3.0/merchants/{merchant_id}/sales"
        sales: list[NormalizedSale] = []
        for page in range(1, _MAX_PAGES + 1):
            params: dict[str, str | int] = {"page": page, "size": _PAGE_SIZE}
            if since is not None:
                params["beginLocalDate"] = since.date().isoformat()
            try:
                response = await client.get(url, headers=headers, params=params)
            except httpx.HTTPError as exc:
                raise ConnectorError("Falha ao buscar vendas no iFood.") from exc
            if response.status_code >= 400:
                raise ConnectorError("O iFood recusou a consulta de vendas.")

            records = _extract_records(response.json())
            for record in records:
                sale = _parse_ifood_sale(record)
                if sale is not None:
                    sales.append(sale)
            if len(records) < _PAGE_SIZE:
                break
        return sales


def _extract_records(payload: object) -> list[dict[str, object]]:
    """Extrai a lista de vendas da resposta, tolerante à chave usada."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("sales", "data", "items", "content"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _parse_ifood_sale(record: dict[str, object]) -> NormalizedSale | None:
    order_id = record.get("orderId") or record.get("id")
    if not isinstance(order_id, str) or not order_id:
        return None

    amount = _extract_amount(record)
    if amount is None or amount == 0:
        return None

    record_type = str(record.get("type", "")).upper()
    is_refund = record_type in _REFUND_TYPES or amount < 0
    amount_cents = abs(round(amount * 100))
    if amount_cents <= 0:
        return None

    occurred_at = (
        _parse_datetime(record.get("date"))
        or _parse_datetime(record.get("createdAt"))
        or datetime.now(UTC)
    )

    customer = record.get("customer") if isinstance(record.get("customer"), dict) else {}
    assert isinstance(customer, dict)
    buyer_name = customer.get("name") if isinstance(customer.get("name"), str) else None

    return NormalizedSale(
        external_id=order_id,
        description=_describe(record, order_id),
        amount_cents=amount_cents,
        occurred_at=occurred_at,
        is_refund=is_refund,
        buyer_name=buyer_name,
        buyer_email=None,
    )


def _describe(record: dict[str, object], order_id: str) -> str:
    items = record.get("items") if isinstance(record.get("items"), list) else []
    assert isinstance(items, list)
    names = [
        item["name"]
        for item in items
        if isinstance(item, dict) and isinstance(item.get("name"), str) and item["name"]
    ]
    if names:
        return ", ".join(names)
    short = record.get("orderIdShort")
    label = short if isinstance(short, str) and short else order_id[:8]
    return f"Pedido iFood #{label}"


def _extract_amount(record: dict[str, object]) -> float | None:
    """Procura o valor total nos caminhos documentados, do mais específico ao
    mais geral."""
    for path in (("bundle", "total", "value"), ("total", "value"), ("amount", "value")):
        value = _dig(record, path)
        if isinstance(value, int | float):
            return float(value)
    for key in ("total", "amount", "value", "grossValue", "netValue"):
        value = record.get(key)
        if isinstance(value, int | float):
            return float(value)
    return None


def _dig(record: dict[str, object], path: tuple[str, ...]) -> object:
    current: object = record
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.strptime(value[:10], "%Y-%m-%d")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed
