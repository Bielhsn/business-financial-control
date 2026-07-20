import httpx

from app.core.exceptions import UnauthorizedError
from app.domain.auth.google import GoogleIdentity

_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


class GoogleTokenInfoVerifier:
    """Valida o id_token do Google pelo endpoint tokeninfo. Simples e sem
    dependências extras; para volume alto, trocar por verificação local de JWT
    com as chaves públicas do Google (mesma porta, outro adaptador).

    `transport` é injetável para os testes usarem httpx.MockTransport."""

    def __init__(
        self,
        *,
        client_id: str,
        tokeninfo_url: str = _TOKENINFO_URL,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._client_id = client_id
        self._tokeninfo_url = tokeninfo_url
        self._transport = transport

    async def verify(self, id_token: str) -> GoogleIdentity:
        try:
            async with httpx.AsyncClient(timeout=15.0, transport=self._transport) as client:
                response = await client.get(self._tokeninfo_url, params={"id_token": id_token})
        except httpx.HTTPError as exc:
            raise UnauthorizedError("Não foi possível validar o login com o Google.") from exc

        if response.status_code >= 400:
            raise UnauthorizedError("Token do Google inválido ou expirado.")

        data = response.json()
        if data.get("aud") != self._client_id:
            raise UnauthorizedError("Token do Google emitido para outro aplicativo.")

        email = data.get("email")
        if not isinstance(email, str) or not email:
            raise UnauthorizedError("O Google não retornou um e-mail.")

        return GoogleIdentity(
            email=email.strip().lower(),
            full_name=str(data.get("name") or email.split("@")[0]),
            email_verified=str(data.get("email_verified", "false")).lower() == "true",
        )
