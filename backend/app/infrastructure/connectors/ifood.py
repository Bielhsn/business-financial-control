"""Conector do iFood: autentica a loja e traduz as vendas para `NormalizedSale`.

Ao contrário dos outros provedores OAuth da plataforma, o iFood **não** tem
authorization-code por redirect — não existe endpoint `/oauth/authorize`, e
apontar para ele devolve o 404 do gateway ("no Route matched with those
values"). O acesso acontece por client_credentials com as chaves do aplicativo da
plataforma — que são da Aurum, não da loja. O lojista não tem (nem deveria ter)
credencial de desenvolvedor: ele informa apenas qual loja dele deve ser lida, e
as chaves ficam no ambiente do servidor. Por isso a autenticação mora aqui, e
não no cliente OAuth genérico (que segue o padrão snake_case correto para
Shopify e Mercado Livre).

Sobre o mapeamento: os nomes dos campos seguem a documentação da API do iFood
(Merchant + Financial). Como o formato exato precisa ser confirmado contra uma
conta real de lojista antes do go-live, todo o parsing fica isolado em funções
puras (`_parse_ifood_sale` e auxiliares), fáceis de ajustar e cobertas por
testes. Assim, no dia em que as credenciais reais existirem, valida-se o formato
e liga-se a sincronização sem tocar no motor de sync, na API ou no frontend.
"""

from datetime import UTC, datetime, timedelta

import httpx

from app.core.exceptions import ConnectorError
from app.domain.connector.entities import NormalizedSale

# Base da API do iFood. Parametrizável no construtor para os testes usarem um
# transporte mock (httpx.MockTransport) sem tocar a rede.
_DEFAULT_BASE_URL = "https://merchant-api.ifood.com.br"
_TOKEN_PATH = "/authentication/v1.0/oauth/token"
_MAX_PAGES = 50
_PAGE_SIZE = 100
# Janela da primeira sincronização, quando ainda não há "desde quando".
_DEFAULT_WINDOW_DAYS = 90

# `type` do registro financeiro que representa estorno/cancelamento (vira despesa).
_REFUND_TYPES = frozenset(
    {"CANCELLATION", "CANCELLED", "CANCELED", "REFUND", "CHARGEBACK", "DISPUTE"}
)


class IFoodConnector:
    """Conector do iFood: troca as chaves do aplicativo por um token e traduz o
    histórico de vendas para `NormalizedSale`."""

    provider = "ifood"

    def __init__(
        self,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        base_url: str = _DEFAULT_BASE_URL,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        # Chaves do aplicativo da Aurum no Portal do Desenvolvedor, vindas do
        # ambiente do servidor. São da plataforma, não da loja: o lojista informa
        # apenas qual loja dele deve ser lida.
        self._client_id = client_id
        self._client_secret = client_secret
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=30.0, transport=self._transport)

    async def _resolve_token(self, client: httpx.AsyncClient, credentials: dict[str, str]) -> str:
        """Obtém o token de acesso com as chaves do aplicativo da plataforma.

        Um `access_token` já guardado ainda é aceito, para conexões criadas antes
        de as chaves migrarem para o ambiente do servidor.
        """
        if self._client_id and self._client_secret:
            return await self._request_token(client, self._client_id, self._client_secret)

        token = credentials.get("access_token", "")
        if token:
            return token

        # Falha de configuração da plataforma, não do lojista — a mensagem
        # precisa dizer isso, senão ele procura um erro que não é dele.
        raise ConnectorError(
            "A integração com o iFood ainda não está configurada nesta instalação. "
            "O responsável pela plataforma precisa definir IFOOD_CLIENT_ID e "
            "IFOOD_CLIENT_SECRET."
        )

    async def _request_token(
        self, client: httpx.AsyncClient, client_id: str, client_secret: str
    ) -> str:
        """Autentica pelo modelo centralizado (client_credentials).

        Atenção ao detalhe que não se descobre lendo a especificação de OAuth2: o
        iFood espera os campos do formulário em **camelCase** (`grantType`,
        `clientId`, `clientSecret`). Enviar o snake_case do padrão OAuth2 é aceito
        pela rota e recusado com "Invalid grant type null" — um erro que parece de
        credencial, mas é de nomenclatura.
        """
        try:
            response = await client.post(
                f"{self._base_url}{_TOKEN_PATH}",
                data={
                    "grantType": "client_credentials",
                    "clientId": client_id,
                    "clientSecret": client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.HTTPError as exc:
            raise ConnectorError("Não foi possível conectar ao iFood.") from exc
        if response.status_code >= 400:
            raise ConnectorError(_token_error_message(response))

        payload = response.json()
        token = payload.get("accessToken") or payload.get("access_token")
        if not isinstance(token, str) or not token:
            raise ConnectorError("O iFood não retornou um token de acesso.")
        return token

    async def test_connection(self, credentials: dict[str, str]) -> None:
        async with self._client() as client:
            token = await self._resolve_token(client, credentials)
            await self._list_merchant_ids(client, token, credentials)

    async def fetch_sales(
        self, credentials: dict[str, str], *, since: datetime | None
    ) -> list[NormalizedSale]:
        async with self._client() as client:
            token = await self._resolve_token(client, credentials)
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
            raise ConnectorError(_ifood_error_message(response, "o acesso à loja"))

        payload = response.json()
        merchants = payload if isinstance(payload, list) else payload.get("merchants", [])
        ids = [
            m["id"]
            for m in merchants
            if isinstance(m, dict) and isinstance(m.get("id"), str) and m["id"]
        ]
        if not ids:
            raise ConnectorError(
                "Nenhuma loja encontrada. Confirme se a loja está vinculada ao "
                "aplicativo da Aurum no portal do iFood."
            )
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
        # A consulta financeira do iFood é por período, e o intervalo não é
        # opcional. Na primeira sincronização não existe "desde quando", então
        # a janela padrão cobre os últimos meses em vez de omitir as datas — o
        # que fazia a API recusar a consulta.
        begin, end = _sales_window(since)
        sales: list[NormalizedSale] = []
        for page in range(1, _MAX_PAGES + 1):
            params: dict[str, str | int] = {
                "page": page,
                "size": _PAGE_SIZE,
                "beginLocalDate": begin,
                "endLocalDate": end,
            }
            try:
                response = await client.get(url, headers=headers, params=params)
            except httpx.HTTPError as exc:
                raise ConnectorError("Falha ao buscar vendas no iFood.") from exc
            if response.status_code >= 400:
                raise ConnectorError(_ifood_error_message(response, "consultar as vendas"))

            records = _extract_records(response.json())
            for record in records:
                sale = _parse_ifood_sale(record)
                if sale is not None:
                    sales.append(sale)
            if len(records) < _PAGE_SIZE:
                break
        return sales


def _sales_window(since: datetime | None) -> tuple[str, str]:
    """Intervalo da consulta financeira, em datas locais (AAAA-MM-DD)."""
    end = datetime.now(UTC).date()
    begin = since.date() if since is not None else end - timedelta(days=_DEFAULT_WINDOW_DAYS)
    return begin.isoformat(), end.isoformat()


def _ifood_detail(response: httpx.Response) -> str:
    """Extrai a mensagem que o iFood devolveu, nos dois formatos que ele usa:
    `{"error": {"message": ...}}` na autenticação e `{"message": ...}` no
    gateway."""
    try:
        payload = response.json()
    except ValueError:
        return ""
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            nested = error.get("message")
            if isinstance(nested, str):
                return nested
        message = payload.get("message")
        if isinstance(message, str):
            return message
    return ""


def _ifood_error_message(response: httpx.Response, acao: str) -> str:
    """Repassa o motivo dado pelo iFood em vez de um "recusou" genérico.

    Sem o motivo original, um 403 de permissão e um 400 de parâmetro chegam ao
    lojista com a mesma frase — e não há como saber o que corrigir.
    """
    detail = _ifood_detail(response)
    sufixo = f": {detail}" if detail else "."
    mensagem = f"O iFood recusou {acao} (HTTP {response.status_code}){sufixo}"

    # 403 aqui é sempre autorização, nunca código: o token é válido (senão viria
    # 401) e a rota existe (senão viria 404). Dizer só "forbidden" deixa quem lê
    # sem saber onde agir, e o lugar não é o Aurum — é o portal do iFood.
    if response.status_code == 403:
        mensagem += (
            " Isso é permissão no iFood, não configuração do Aurum: o aplicativo "
            "precisa ter o módulo financeiro liberado e a loja vinculada a ele no "
            "Portal do Desenvolvedor."
        )
    return mensagem


def _token_error_message(response: httpx.Response) -> str:
    detail = _ifood_detail(response)
    sufixo = f" ({detail})" if detail else ""
    return f"O iFood recusou as credenciais do aplicativo{sufixo}."


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
