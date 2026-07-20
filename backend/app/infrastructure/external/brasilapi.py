import httpx

from app.core.exceptions import ConnectorError, NotFoundError
from app.domain.company.cnpj_lookup import CnpjInfo

_DEFAULT_BASE_URL = "https://brasilapi.com.br/api/cnpj/v1"
_ACTIVE_STATUS = "ATIVA"


class BrasilApiCnpjLookup:
    """Consulta CNPJ na BrasilAPI (pública, sem chave). `transport` é injetável
    para os testes usarem httpx.MockTransport sem tocar a rede."""

    def __init__(
        self,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    async def fetch(self, cnpj: str) -> CnpjInfo:
        try:
            async with httpx.AsyncClient(timeout=15.0, transport=self._transport) as client:
                response = await client.get(f"{self._base_url}/{cnpj}")
        except httpx.HTTPError as exc:
            raise ConnectorError("Não foi possível consultar a Receita agora.") from exc

        if response.status_code == 404:
            raise NotFoundError("CNPJ não encontrado na base da Receita.")
        if response.status_code >= 400:
            raise ConnectorError("A consulta de CNPJ falhou. Tente novamente em instantes.")

        data = response.json()
        status = data.get("descricao_situacao_cadastral") or data.get("situacao")
        return CnpjInfo(
            cnpj=cnpj,
            legal_name=_clean(data.get("razao_social")),
            trade_name=_clean(data.get("nome_fantasia")),
            status=_clean(status),
            is_active=isinstance(status, str) and status.strip().upper() == _ACTIVE_STATUS,
            city=_clean(data.get("municipio")),
            state=_clean(data.get("uf")),
            email=_clean(data.get("email")),
            phone=_clean(data.get("ddd_telefone_1")),
            main_activity=_clean(data.get("cnae_fiscal_descricao")),
        )


def _clean(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
