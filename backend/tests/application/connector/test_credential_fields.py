"""Obrigatoriedade dos campos de credencial.

O padrão do produto é pedir o par completo (Client ID + Client Secret), porque é
o formato da maioria dos provedores. Mas nem todos entregam os dois: alguns dão
só uma chave de API. Exigir um campo que não existe do outro lado trava a
conexão sem motivo, então cada provedor declara o que é essencial — e dispensar
é a exceção, sempre explícita.
"""

import pytest

from app.application.connector.connect_provider import split_credentials
from app.core.exceptions import ValidationError
from app.domain.connector.registry import (
    CONNECTOR_REGISTRY,
    ConnectorDefinition,
    CredentialField,
)


def test_credential_field_is_required_by_default() -> None:
    """O padrão precisa ser o seguro: quem dispensa um campo declara isso."""
    assert CredentialField("api_key", "API Key").required is True


def test_optional_field_left_blank_does_not_block_the_connection(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    definicao = ConnectorDefinition(
        provider="provedor_teste",
        name="Provedor de Teste",
        group="Testes",
        description="",
        credential_fields=(
            CredentialField("api_key", "API Key", secret=True),
            CredentialField("client_secret", "Client Secret", secret=True, required=False),
        ),
        capabilities=(),
    )
    monkeypatch.setattr(
        "app.application.connector.connect_provider.get_connector_definition",
        lambda provider: definicao,
    )

    secrets, config = split_credentials("provedor_teste", {"api_key": "chave-real"})

    assert secrets == {"api_key": "chave-real"}
    # Opcional em branco não vira credencial vazia: guardar "" faria o conector
    # enviar um campo vazio ao provedor, que é diferente de não enviar.
    assert "client_secret" not in secrets
    assert config == {}


def test_required_field_left_blank_still_blocks(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    definicao = ConnectorDefinition(
        provider="provedor_teste",
        name="Provedor de Teste",
        group="Testes",
        description="",
        credential_fields=(CredentialField("api_key", "API Key", secret=True),),
        capabilities=(),
    )
    monkeypatch.setattr(
        "app.application.connector.connect_provider.get_connector_definition",
        lambda provider: definicao,
    )

    with pytest.raises(ValidationError, match="API Key"):
        split_credentials("provedor_teste", {})


def test_ifood_still_requires_the_secret() -> None:
    """A API do iFood responde "Client secret is mandatory" quando o campo não
    vai no corpo — verificado contra o endpoint real. Marcar como opcional
    deixaria o formulário passar para um erro do provedor logo em seguida."""
    ifood = next(item for item in CONNECTOR_REGISTRY if item.provider == "ifood")
    secret = next(f for f in ifood.credential_fields if f.key == "client_secret")

    assert secret.required is True
