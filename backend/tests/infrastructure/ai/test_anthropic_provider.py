from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import httpx
import pytest

from app.core.config import Settings
from app.core.exceptions import AIProviderError
from app.domain.company.entities import Company
from app.domain.dashboard.kpi_registry import KPIMetric
from app.infrastructure.ai.anthropic_provider import AnthropicAIProvider

pytestmark = pytest.mark.anyio


class _FakeBlock:
    def __init__(self, block_type: str, input_: dict[str, Any]) -> None:
        self.type = block_type
        self.input = input_


def _company() -> Company:
    now = datetime.now(UTC)
    return Company(
        id="1",
        name="Barbearia do Zé",
        segment="Barbearia",
        employee_count=3,
        average_customer_count=100,
        city="São Paulo",
        state="SP",
        country="Brasil",
        size="Pequena",
        tax_regime=None,
        additional_info=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def _settings() -> Settings:
    return Settings(_env_file=None, anthropic_api_key="sk-test")


@patch("app.infrastructure.ai.anthropic_provider.anthropic.AsyncAnthropic")
async def test_generate_company_blueprint_parses_tool_use_response(
    mock_client_cls: MagicMock,
) -> None:
    mock_response = MagicMock()
    mock_response.content = [
        _FakeBlock(
            "tool_use",
            {
                "modules": ["financial_core", "clients"],
                "financial_categories": [{"name": "Vendas", "type": "income"}],
                "kpis": [
                    {
                        "key": "average_ticket",
                        "name": "Ticket médio",
                        "description": "...",
                        "metric": "average_ticket",
                    }
                ],
                "client_custom_fields": [
                    {"key": "favorite_service", "label": "Serviço favorito", "type": "text"}
                ],
            },
        )
    ]
    mock_client_cls.return_value.messages.create = AsyncMock(return_value=mock_response)

    provider = AnthropicAIProvider(_settings())
    draft = await provider.generate_company_blueprint(company=_company(), additional_context=None)

    assert draft.modules == ["financial_core", "clients"]
    assert draft.financial_categories[0].name == "Vendas"
    assert draft.kpis[0].key == "average_ticket"
    assert draft.kpis[0].metric == KPIMetric.AVERAGE_TICKET
    assert draft.client_custom_fields[0].key == "favorite_service"


@patch("app.infrastructure.ai.anthropic_provider.anthropic.AsyncAnthropic")
async def test_raises_when_no_tool_use_block_is_returned(mock_client_cls: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.content = [_FakeBlock("text", {})]
    mock_client_cls.return_value.messages.create = AsyncMock(return_value=mock_response)

    provider = AnthropicAIProvider(_settings())

    with pytest.raises(AIProviderError):
        await provider.generate_company_blueprint(company=_company(), additional_context=None)


@patch("app.infrastructure.ai.anthropic_provider.anthropic.AsyncAnthropic")
async def test_filters_out_hallucinated_module_ids(mock_client_cls: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.content = [
        _FakeBlock(
            "tool_use",
            {
                "modules": ["financial_core", "not-a-real-module"],
                "financial_categories": [{"name": "Vendas", "type": "income"}],
                "kpis": [{"key": "x", "name": "X", "description": "Y", "metric": "total_revenue"}],
                "client_custom_fields": [],
            },
        )
    ]
    mock_client_cls.return_value.messages.create = AsyncMock(return_value=mock_response)

    provider = AnthropicAIProvider(_settings())
    draft = await provider.generate_company_blueprint(company=_company(), additional_context=None)

    assert draft.modules == ["financial_core"]


@patch("app.infrastructure.ai.anthropic_provider.anthropic.AsyncAnthropic")
async def test_raises_on_malformed_tool_input(mock_client_cls: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.content = [_FakeBlock("tool_use", {"modules": ["financial_core"]})]
    mock_client_cls.return_value.messages.create = AsyncMock(return_value=mock_response)

    provider = AnthropicAIProvider(_settings())

    with pytest.raises(AIProviderError):
        await provider.generate_company_blueprint(company=_company(), additional_context=None)


@patch("app.infrastructure.ai.anthropic_provider.anthropic.AsyncAnthropic")
async def test_wraps_api_errors(mock_client_cls: MagicMock) -> None:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    mock_client_cls.return_value.messages.create = AsyncMock(
        side_effect=anthropic.APIConnectionError(request=request)
    )

    provider = AnthropicAIProvider(_settings())

    with pytest.raises(AIProviderError):
        await provider.generate_company_blueprint(company=_company(), additional_context=None)


@patch("app.infrastructure.ai.anthropic_provider.anthropic.AsyncAnthropic")
async def test_raises_when_every_suggested_module_is_invalid(mock_client_cls: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.content = [
        _FakeBlock(
            "tool_use",
            {
                "modules": ["not-real-1", "not-real-2"],
                "financial_categories": [{"name": "Vendas", "type": "income"}],
                "kpis": [{"key": "x", "name": "X", "description": "Y", "metric": "total_revenue"}],
                "client_custom_fields": [],
            },
        )
    ]
    mock_client_cls.return_value.messages.create = AsyncMock(return_value=mock_response)

    provider = AnthropicAIProvider(_settings())

    with pytest.raises(AIProviderError):
        await provider.generate_company_blueprint(company=_company(), additional_context=None)


@patch("app.infrastructure.ai.anthropic_provider.anthropic.AsyncAnthropic")
async def test_prompt_includes_company_additional_info_and_extra_context(
    mock_client_cls: MagicMock,
) -> None:
    mock_response = MagicMock()
    mock_response.content = [
        _FakeBlock(
            "tool_use",
            {
                "modules": ["financial_core"],
                "financial_categories": [{"name": "Vendas", "type": "income"}],
                "kpis": [{"key": "x", "name": "X", "description": "Y", "metric": "total_revenue"}],
                "client_custom_fields": [],
            },
        )
    ]
    mock_create = AsyncMock(return_value=mock_response)
    mock_client_cls.return_value.messages.create = mock_create

    company = _company()
    company.additional_info = "Loja física e online."
    provider = AnthropicAIProvider(_settings())

    await provider.generate_company_blueprint(
        company=company, additional_context="Cresceu 30% este ano."
    )

    sent_prompt = mock_create.call_args.kwargs["messages"][0]["content"]
    assert "Loja física e online." in sent_prompt
    assert "Cresceu 30% este ano." in sent_prompt


@patch("app.infrastructure.ai.anthropic_provider.anthropic.AsyncAnthropic")
async def test_raises_when_kpi_metric_is_invalid(mock_client_cls: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.content = [
        _FakeBlock(
            "tool_use",
            {
                "modules": ["financial_core"],
                "financial_categories": [{"name": "Vendas", "type": "income"}],
                "kpis": [
                    {"key": "x", "name": "X", "description": "Y", "metric": "not-a-real-metric"}
                ],
                "client_custom_fields": [],
            },
        )
    ]
    mock_client_cls.return_value.messages.create = AsyncMock(return_value=mock_response)

    provider = AnthropicAIProvider(_settings())

    with pytest.raises(AIProviderError):
        await provider.generate_company_blueprint(company=_company(), additional_context=None)
