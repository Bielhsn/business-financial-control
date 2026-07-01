from typing import Any

import anthropic
from anthropic.types import MessageParam, ToolChoiceToolParam, ToolParam

from app.core.config import Settings
from app.core.exceptions import AIProviderError
from app.domain.blueprint.entities import (
    CustomFieldDefinition,
    CustomFieldType,
    FinancialCategory,
    FinancialCategoryType,
    KPIDefinition,
)
from app.domain.blueprint.module_registry import MODULE_IDS, MODULE_REGISTRY
from app.domain.blueprint.ports import CompanyBlueprintDraft
from app.domain.company.entities import Company

_TOOL_NAME = "submit_company_blueprint"
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
                        },
                        "required": ["key", "name", "description"],
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
    lines = [
        "Você é um especialista em estruturar dashboards financeiros para empresas de "
        "qualquer segmento.",
        f"Catálogo de módulos disponíveis:\n{modules_catalog}",
        "Dados da empresa:",
        f"- Nome: {company.name}",
        f"- Segmento: {company.segment}",
        f"- Porte: {company.size}",
        f"- Número de funcionários: {company.employee_count}",
        f"- Quantidade média de clientes: {company.average_customer_count}",
        f"- Localização: {company.city}/{company.state}, {company.country}",
        f"- Regime tributário: {company.tax_regime or 'não informado'}",
    ]
    if company.additional_info:
        lines.append(f"- Informações adicionais da empresa: {company.additional_info}")
    if additional_context:
        lines.append(f"Informações adicionais fornecidas agora pelo usuário: {additional_context}")
    lines.append(
        "Com base nesses dados, selecione os módulos mais adequados do catálogo (nunca "
        "invente módulos fora da lista), sugira categorias financeiras de receita e "
        "despesa típicas deste segmento, indicadores financeiros (KPIs) relevantes e, se "
        "fizer sentido, campos personalizados para o cadastro de clientes. Responda "
        "apenas chamando a ferramenta fornecida."
    )
    return "\n".join(lines)


def _parse_blueprint(data: dict[str, Any]) -> CompanyBlueprintDraft:
    try:
        modules = [module_id for module_id in data["modules"] if module_id in MODULE_IDS]
        financial_categories = [
            FinancialCategory(name=item["name"], type=FinancialCategoryType(item["type"]))
            for item in data["financial_categories"]
        ]
        kpis = [
            KPIDefinition(key=item["key"], name=item["name"], description=item["description"])
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
