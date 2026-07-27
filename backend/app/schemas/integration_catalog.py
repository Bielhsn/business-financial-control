from pydantic import BaseModel

from app.domain.blueprint.integration_registry import INTEGRATION_REGISTRY


class IntegrationCatalogItemResponse(BaseModel):
    """Uma plataforma que a Aurum conhece.

    `connectable` diz se existe conector implementado — ou seja, se o botão
    "Conectar" leva a um fluxo real. O resto do catálogo mostra o que o produto
    suporta, sem prometer uma conexão que ainda não existe.
    """

    id: str
    name: str
    group: str
    connectable: bool


class IntegrationCatalogResponse(BaseModel):
    items: list[IntegrationCatalogItemResponse]


def build_integration_catalog() -> IntegrationCatalogResponse:
    return IntegrationCatalogResponse(
        items=[
            IntegrationCatalogItemResponse(
                id=item.id,
                name=item.name,
                group=item.group,
                connectable=item.is_connectable,
            )
            for item in INTEGRATION_REGISTRY
        ]
    )
