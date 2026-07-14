from app.core.exceptions import ValidationError
from app.domain.blueprint.repository import CompanyBlueprintRepository


async def validate_custom_fields(
    *,
    company_id: str,
    custom_fields: dict[str, str],
    blueprint_repository: CompanyBlueprintRepository,
) -> None:
    """Garante que toda chave enviada existe nos campos personalizados de cliente
    sugeridos pelo Company Blueprint (Etapa 4) — evita dados soltos sem relação
    com a estrutura pensada para o segmento da empresa."""
    if not custom_fields:
        return

    blueprint = await blueprint_repository.get_by_company_id(company_id)
    allowed_keys = (
        {field.key for field in blueprint.client_custom_fields} if blueprint is not None else set()
    )

    unknown_keys = set(custom_fields) - allowed_keys
    if unknown_keys:
        raise ValidationError(
            "Campos personalizados desconhecidos para esta empresa.",
            details={"unknown_fields": sorted(unknown_keys)},
        )
