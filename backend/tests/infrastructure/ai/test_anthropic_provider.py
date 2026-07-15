from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import httpx
import pytest

from app.core.config import Settings
from app.core.exceptions import AIProviderError
from app.domain.company.entities import Company
from app.domain.dashboard.entities import (
    CategoryBreakdown,
    DashboardSummary,
    MonthlyBreakdown,
    PeriodComparison,
)
from app.domain.dashboard.kpi_registry import KPIMetric
from app.domain.insights.entities import InsightKind
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
    company.currency = "USD"
    company.sales_channels = ["Loja física", "WhatsApp"]
    company.sales_mode = "Agendamento"
    company.main_offerings = "Cortes e pomadas"
    provider = AnthropicAIProvider(_settings())

    await provider.generate_company_blueprint(
        company=company, additional_context="Cresceu 30% este ano."
    )

    sent_prompt = mock_create.call_args.kwargs["messages"][0]["content"]
    assert "Loja física e online." in sent_prompt
    assert "Cresceu 30% este ano." in sent_prompt
    assert "Moeda de operação: USD" in sent_prompt
    assert "Canais de venda: Loja física, WhatsApp" in sent_prompt
    assert "Forma de venda: Agendamento" in sent_prompt
    assert "Principais produtos/serviços: Cortes e pomadas" in sent_prompt


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


def _summary() -> DashboardSummary:
    return DashboardSummary(
        start=datetime(2026, 6, 1, tzinfo=UTC),
        end=datetime(2026, 6, 30, tzinfo=UTC),
        revenue_cents=1500000,
        expense_cents=500000,
        profit_cents=1000000,
        profit_margin_pct=66.7,
        average_ticket_cents=15000,
        transaction_count=42,
        active_clients=12,
        monthly_breakdown=[
            MonthlyBreakdown(
                year=2026,
                month=6,
                revenue_cents=1500000,
                expense_cents=500000,
                profit_cents=1000000,
            )
        ],
        top_income_categories=[
            CategoryBreakdown(category_id="c1", category_name="Vendas", total_cents=1500000)
        ],
        top_expense_categories=[
            CategoryBreakdown(category_id="c2", category_name="Aluguel", total_cents=500000)
        ],
        comparison=PeriodComparison(
            revenue_change_pct=25.0, expense_change_pct=10.0, profit_change_pct=30.0
        ),
        kpis=[],
    )


@patch("app.infrastructure.ai.anthropic_provider.anthropic.AsyncAnthropic")
async def test_generate_financial_insights_parses_tool_use_response(
    mock_client_cls: MagicMock,
) -> None:
    mock_response = MagicMock()
    mock_response.content = [
        _FakeBlock(
            "tool_use",
            {
                "insights": [
                    {"kind": "highlight", "title": "Bom lucro", "message": "Margem alta."},
                    {"kind": "warning", "title": "Despesa subiu", "message": "Atenção."},
                ]
            },
        )
    ]
    mock_create = AsyncMock(return_value=mock_response)
    mock_client_cls.return_value.messages.create = mock_create

    provider = AnthropicAIProvider(_settings())
    insights = await provider.generate_financial_insights(company=_company(), summary=_summary())

    assert len(insights) == 2
    assert insights[0].kind == InsightKind.HIGHLIGHT
    # O prompt inclui os números já computados (a IA não calcula nada).
    sent_prompt = mock_create.call_args.kwargs["messages"][0]["content"]
    assert "R$ 15000.00" in sent_prompt
    assert "Vendas" in sent_prompt


@patch("app.infrastructure.ai.anthropic_provider.anthropic.AsyncAnthropic")
async def test_generate_financial_insights_raises_on_invalid_kind(
    mock_client_cls: MagicMock,
) -> None:
    mock_response = MagicMock()
    mock_response.content = [
        _FakeBlock(
            "tool_use",
            {"insights": [{"kind": "not-a-kind", "title": "X", "message": "Y"}]},
        )
    ]
    mock_client_cls.return_value.messages.create = AsyncMock(return_value=mock_response)

    provider = AnthropicAIProvider(_settings())

    with pytest.raises(AIProviderError):
        await provider.generate_financial_insights(company=_company(), summary=_summary())


@patch("app.infrastructure.ai.anthropic_provider.anthropic.AsyncAnthropic")
async def test_generate_financial_insights_raises_on_empty_list(
    mock_client_cls: MagicMock,
) -> None:
    mock_response = MagicMock()
    mock_response.content = [_FakeBlock("tool_use", {"insights": []})]
    mock_client_cls.return_value.messages.create = AsyncMock(return_value=mock_response)

    provider = AnthropicAIProvider(_settings())

    with pytest.raises(AIProviderError):
        await provider.generate_financial_insights(company=_company(), summary=_summary())


class _FakeTextBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


@patch("app.infrastructure.ai.anthropic_provider.anthropic.AsyncAnthropic")
async def test_generate_period_summary_returns_text(mock_client_cls: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.content = [_FakeTextBlock("Mês sólido, com lucro de R$ 10.000,00.")]
    mock_create = AsyncMock(return_value=mock_response)
    mock_client_cls.return_value.messages.create = mock_create

    provider = AnthropicAIProvider(_settings())
    text = await provider.generate_period_summary(company=_company(), summary=_summary())

    assert "Mês sólido" in text
    sent_prompt = mock_create.call_args.kwargs["messages"][0]["content"]
    # O prompt de texto compartilha o mesmo bloco de números dos insights.
    assert "R$ 15000.00" in sent_prompt
    assert "resumo executivo" in sent_prompt


@patch("app.infrastructure.ai.anthropic_provider.anthropic.AsyncAnthropic")
async def test_answer_financial_question_includes_question(mock_client_cls: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.content = [_FakeTextBlock("Sua maior despesa é Aluguel.")]
    mock_create = AsyncMock(return_value=mock_response)
    mock_client_cls.return_value.messages.create = mock_create

    provider = AnthropicAIProvider(_settings())
    answer = await provider.answer_financial_question(
        company=_company(), summary=_summary(), question="Qual minha maior despesa?"
    )

    assert answer == "Sua maior despesa é Aluguel."
    sent_prompt = mock_create.call_args.kwargs["messages"][0]["content"]
    assert "Qual minha maior despesa?" in sent_prompt


@patch("app.infrastructure.ai.anthropic_provider.anthropic.AsyncAnthropic")
async def test_text_completion_raises_on_empty_response(mock_client_cls: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.content = []
    mock_client_cls.return_value.messages.create = AsyncMock(return_value=mock_response)

    provider = AnthropicAIProvider(_settings())

    with pytest.raises(AIProviderError):
        await provider.generate_period_summary(company=_company(), summary=_summary())


@patch("app.infrastructure.ai.anthropic_provider.anthropic.AsyncAnthropic")
async def test_blueprint_filters_unknown_integrations(mock_client_cls: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.content = [
        _FakeBlock(
            "tool_use",
            {
                "modules": ["financial_core"],
                "financial_categories": [{"name": "Vendas", "type": "income"}],
                "kpis": [
                    {
                        "key": "x",
                        "name": "X",
                        "description": "Y",
                        "metric": "total_revenue",
                    }
                ],
                "client_custom_fields": [],
                "integrations": ["whatsapp", "integracao-inventada", "shopify"],
            },
        )
    ]
    mock_create = AsyncMock(return_value=mock_response)
    mock_client_cls.return_value.messages.create = mock_create

    provider = AnthropicAIProvider(_settings())
    draft = await provider.generate_company_blueprint(company=_company(), additional_context=None)

    # Defesa em profundidade: ids fora do catálogo são descartados silenciosamente.
    assert draft.integrations == ["whatsapp", "shopify"]
    # O prompt apresenta o catálogo de integrações à IA.
    sent_prompt = mock_create.call_args.kwargs["messages"][0]["content"]
    assert "Catálogo de integrações disponíveis:" in sent_prompt
    assert "- ifood: iFood (Delivery)" in sent_prompt
