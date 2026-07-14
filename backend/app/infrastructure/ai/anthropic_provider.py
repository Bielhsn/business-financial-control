from typing import Any

import anthropic
from anthropic.types import MessageParam, ToolChoiceToolParam, ToolParam

from app.core.config import Settings
from app.core.exceptions import AIProviderError
from app.domain.blueprint.entities import (
    CustomFieldDefinition,
    CustomFieldType,
    KPIDefinition,
    SuggestedFinancialCategory,
)
from app.domain.blueprint.module_registry import MODULE_IDS, MODULE_REGISTRY
from app.domain.blueprint.ports import CompanyBlueprintDraft
from app.domain.company.entities import Company
from app.domain.dashboard.entities import DashboardSummary
from app.domain.dashboard.kpi_registry import KPI_METRIC_REGISTRY, KPIMetric
from app.domain.financial.entities import FinancialCategoryType
from app.domain.insights.entities import FinancialInsight, InsightKind

_TOOL_NAME = "submit_company_blueprint"
_INSIGHTS_TOOL_NAME = "submit_financial_insights"
_MAX_TOKENS = 2048


def _build_tool_schema() -> ToolParam:
    module_ids = [module.id for module in MODULE_REGISTRY]
    return {
        "name": _TOOL_NAME,
        "description": "Envia a estrutura de dashboard financeiro sugerida para a empresa.",
        "input_schema": {
            "type": "object",
            "properties": {
                "modules": {
                    "type": "array",
                    "description": "Módulos a ativar para esta empresa.",
                    "items": {"type": "string", "enum": module_ids},
                    "minItems": 1,
                },
                "financial_categories": {
                    "type": "array",
                    "description": (
                        "Categorias financeiras de receita e despesa adequadas ao segmento."
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string", "enum": ["income", "expense"]},
                        },
                        "required": ["name", "type"],
                    },
                    "minItems": 1,
                },
                "kpis": {
                    "type": "array",
                    "description": "Indicadores financeiros relevantes para o segmento.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"},
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "metric": {
                                "type": "string",
                                "enum": [m.metric.value for m in KPI_METRIC_REGISTRY],
                            },
                        },
                        "required": ["key", "name", "description", "metric"],
                    },
                    "minItems": 1,
                },
                "client_custom_fields": {
                    "type": "array",
                    "description": "Campos extras para o cadastro de clientes deste segmento.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"},
                            "label": {"type": "string"},
                            "type": {
                                "type": "string",
                                "enum": ["text", "number", "date", "boolean", "select"],
                            },
                        },
                        "required": ["key", "label", "type"],
                    },
                },
            },
            "required": ["modules", "financial_categories", "kpis", "client_custom_fields"],
        },
    }


def _build_prompt(company: Company, additional_context: str | None) -> str:
    modules_catalog = "\n".join(
        f"- {module.id}: {module.name} — {module.description}" for module in MODULE_REGISTRY
    )
    metrics_catalog = "\n".join(
        f"- {definition.metric.value}: {definition.description}"
        for definition in KPI_METRIC_REGISTRY
    )
    lines = [
        "Você é um especialista em estruturar dashboards financeiros para empresas de "
        "qualquer segmento.",
        f"Catálogo de módulos disponíveis:\n{modules_catalog}",
        f"Catálogo de métricas computáveis disponíveis para KPIs:\n{metrics_catalog}",
        "Dados da empresa:",
        f"- Nome: {company.name}",
        f"- Segmento: {company.segment}",
        f"- Porte: {company.size}",
        f"- Número de funcionários: {company.employee_count}",
        f"- Quantidade média de clientes: {company.average_customer_count}",
        f"- Localização: {company.city}/{company.state}, {company.country}",
        f"- Regime tributário: {company.tax_regime or 'não informado'}",
        f"- Moeda de operação: {company.currency}",
    ]
    if company.sales_channels:
        lines.append(f"- Canais de venda: {', '.join(company.sales_channels)}")
    if company.sales_mode:
        lines.append(f"- Forma de venda: {company.sales_mode}")
    if company.main_offerings:
        lines.append(f"- Principais produtos/serviços: {company.main_offerings}")
    if company.additional_info:
        lines.append(f"- Informações adicionais da empresa: {company.additional_info}")
    if additional_context:
        lines.append(f"Informações adicionais fornecidas agora pelo usuário: {additional_context}")
    lines.append(
        "Com base nesses dados, selecione os módulos mais adequados do catálogo (nunca "
        "invente módulos fora da lista), sugira categorias financeiras de receita e "
        "despesa típicas deste segmento, indicadores financeiros (KPIs) relevantes — cada "
        "um associado a uma métrica computável do catálogo acima, com nome e descrição em "
        "português adequados ao segmento — e, se fizer sentido, campos personalizados para "
        "o cadastro de clientes. Responda apenas chamando a ferramenta fornecida."
    )
    return "\n".join(lines)


def _parse_blueprint(data: dict[str, Any]) -> CompanyBlueprintDraft:
    try:
        modules = [module_id for module_id in data["modules"] if module_id in MODULE_IDS]
        financial_categories = [
            SuggestedFinancialCategory(name=item["name"], type=FinancialCategoryType(item["type"]))
            for item in data["financial_categories"]
        ]
        kpis = [
            KPIDefinition(
                key=item["key"],
                name=item["name"],
                description=item["description"],
                metric=KPIMetric(item["metric"]),
            )
            for item in data["kpis"]
        ]
        client_custom_fields = [
            CustomFieldDefinition(
                key=item["key"], label=item["label"], type=CustomFieldType(item["type"])
            )
            for item in data.get("client_custom_fields", [])
        ]
    except (KeyError, TypeError, ValueError) as exc:
        raise AIProviderError("Resposta da IA em formato inesperado.") from exc

    if not modules:
        raise AIProviderError("A IA não sugeriu nenhum módulo válido para esta empresa.")

    return CompanyBlueprintDraft(
        modules=modules,
        financial_categories=financial_categories,
        kpis=kpis,
        client_custom_fields=client_custom_fields,
    )


def _build_insights_tool_schema() -> ToolParam:
    return {
        "name": _INSIGHTS_TOOL_NAME,
        "description": "Envia os insights financeiros sobre o período analisado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "insights": {
                    "type": "array",
                    "description": "Insights sobre a saúde financeira do período.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "kind": {
                                "type": "string",
                                "enum": [kind.value for kind in InsightKind],
                            },
                            "title": {"type": "string"},
                            "message": {"type": "string"},
                        },
                        "required": ["kind", "title", "message"],
                    },
                    "minItems": 2,
                    "maxItems": 6,
                },
            },
            "required": ["insights"],
        },
    }


def _format_cents(cents: int) -> str:
    return f"R$ {cents / 100:.2f}"


def _build_insights_prompt(company: Company, summary: DashboardSummary) -> str:
    monthly = "\n".join(
        f"- {item.month:02d}/{item.year}: receita {_format_cents(item.revenue_cents)}, "
        f"despesa {_format_cents(item.expense_cents)}, lucro {_format_cents(item.profit_cents)}"
        for item in summary.monthly_breakdown
    )
    top_income = ", ".join(
        f"{item.category_name} ({_format_cents(item.total_cents)})"
        for item in summary.top_income_categories
    )
    top_expense = ", ".join(
        f"{item.category_name} ({_format_cents(item.total_cents)})"
        for item in summary.top_expense_categories
    )

    def pct(value: float | None) -> str:
        return f"{value:+.1f}%" if value is not None else "sem base de comparação"

    lines = [
        "Você é um consultor financeiro para pequenas e médias empresas no Brasil.",
        f"Empresa: {company.name} — segmento: {company.segment}, porte: {company.size}.",
        f"Período analisado: {summary.start:%d/%m/%Y} a {summary.end:%d/%m/%Y}.",
        "Números do período (já calculados pelo sistema — não recalcule):",
        f"- Receita: {_format_cents(summary.revenue_cents)} "
        f"({pct(summary.comparison.revenue_change_pct)} vs. período anterior)",
        f"- Despesas: {_format_cents(summary.expense_cents)} "
        f"({pct(summary.comparison.expense_change_pct)} vs. período anterior)",
        f"- Lucro: {_format_cents(summary.profit_cents)} "
        f"({pct(summary.comparison.profit_change_pct)} vs. período anterior)",
        "- Margem de lucro: "
        + (
            f"{summary.profit_margin_pct:.1f}%"
            if summary.profit_margin_pct is not None
            else "não aplicável (sem receita)"
        ),
        f"- Ticket médio: {_format_cents(summary.average_ticket_cents)}",
        f"- Lançamentos no período: {summary.transaction_count}",
        f"- Clientes ativos: {summary.active_clients}",
        f"Evolução mensal:\n{monthly or '- sem dados'}",
        f"Principais categorias de receita: {top_income or 'nenhuma'}",
        f"Principais categorias de despesa: {top_expense or 'nenhuma'}",
        "Gere de 2 a 6 insights curtos e acionáveis em português: destaques positivos "
        "(highlight), alertas de risco (warning) e oportunidades de melhoria "
        "(opportunity). Considere sazonalidade e tendência a partir da evolução mensal "
        "quando houver dados suficientes. Baseie-se apenas nos números fornecidos — "
        "nunca invente valores. Responda apenas chamando a ferramenta fornecida.",
    ]
    return "\n".join(lines)


def _parse_insights(data: dict[str, Any]) -> list[FinancialInsight]:
    try:
        insights = [
            FinancialInsight(
                kind=InsightKind(item["kind"]),
                title=item["title"],
                message=item["message"],
            )
            for item in data["insights"]
        ]
    except (KeyError, TypeError, ValueError) as exc:
        raise AIProviderError("Resposta da IA em formato inesperado.") from exc

    if not insights:
        raise AIProviderError("A IA não retornou nenhum insight.")
    return insights


def _grounding_context(company: Company, summary: DashboardSummary) -> str:
    """Bloco de números compartilhado pelos prompts de resumo e de perguntas."""
    return _build_insights_prompt(company, summary).rsplit("Gere de 2 a 6 insights", 1)[0]


class AnthropicAIProvider:
    """Adapter para a API da Anthropic (Claude). Assume que a API key já foi validada."""

    def __init__(self, settings: Settings) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.ai_model

    async def generate_company_blueprint(
        self, *, company: Company, additional_context: str | None
    ) -> CompanyBlueprintDraft:
        tool = _build_tool_schema()

        tool_choice: ToolChoiceToolParam = {"type": "tool", "name": _TOOL_NAME}
        messages: list[MessageParam] = [
            {"role": "user", "content": _build_prompt(company, additional_context)}
        ]

        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=_MAX_TOKENS,
                tools=[tool],
                tool_choice=tool_choice,
                messages=messages,
            )
        except anthropic.APIError as exc:
            raise AIProviderError("Falha ao consultar o provedor de IA.") from exc

        tool_use_block = next(
            (block for block in response.content if block.type == "tool_use"), None
        )
        if tool_use_block is None:
            raise AIProviderError("O provedor de IA não retornou uma resposta estruturada válida.")

        return _parse_blueprint(tool_use_block.input)

    async def generate_financial_insights(
        self, *, company: Company, summary: DashboardSummary
    ) -> list[FinancialInsight]:
        tool = _build_insights_tool_schema()
        tool_choice: ToolChoiceToolParam = {"type": "tool", "name": _INSIGHTS_TOOL_NAME}
        messages: list[MessageParam] = [
            {"role": "user", "content": _build_insights_prompt(company, summary)}
        ]

        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=_MAX_TOKENS,
                tools=[tool],
                tool_choice=tool_choice,
                messages=messages,
            )
        except anthropic.APIError as exc:
            raise AIProviderError("Falha ao consultar o provedor de IA.") from exc

        tool_use_block = next(
            (block for block in response.content if block.type == "tool_use"), None
        )
        if tool_use_block is None:
            raise AIProviderError("O provedor de IA não retornou uma resposta estruturada válida.")

        return _parse_insights(tool_use_block.input)

    async def generate_period_summary(self, *, company: Company, summary: DashboardSummary) -> str:
        prompt = _grounding_context(company, summary) + (
            "Escreva um resumo executivo do período em um único parágrafo (máximo 5 "
            "frases), em português, direto e sem jargão: como foi o resultado, o que "
            "mais pesou e para onde a tendência aponta. Use apenas os números "
            "fornecidos — nunca invente valores. Responda somente com o parágrafo."
        )
        return await self._complete_text(prompt)

    async def answer_financial_question(
        self, *, company: Company, summary: DashboardSummary, question: str
    ) -> str:
        prompt = _grounding_context(company, summary) + (
            "Responda à pergunta do usuário em português, em no máximo 4 frases, "
            "estritamente a partir dos números acima. Se os dados fornecidos não "
            "forem suficientes para responder, diga isso explicitamente e sugira o "
            "que registrar no sistema para ter a resposta. Nunca invente valores.\n"
            f"Pergunta do usuário: {question}"
        )
        return await self._complete_text(prompt)

    async def _complete_text(self, prompt: str) -> str:
        messages: list[MessageParam] = [{"role": "user", "content": prompt}]
        try:
            response = await self._client.messages.create(
                model=self._model, max_tokens=1024, messages=messages
            )
        except anthropic.APIError as exc:
            raise AIProviderError("Falha ao consultar o provedor de IA.") from exc

        text = "".join(block.text for block in response.content if block.type == "text").strip()
        if not text:
            raise AIProviderError("O provedor de IA não retornou uma resposta.")
        return text
