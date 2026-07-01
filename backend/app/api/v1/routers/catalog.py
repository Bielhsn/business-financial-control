from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import (
    get_catalog_item_repository,
    get_company_context,
    get_current_user,
    get_stock_movement_repository,
    require_role,
)
from app.application.catalog.adjust_stock import AdjustStockUseCase
from app.application.catalog.create_item import CreateCatalogItemUseCase
from app.application.catalog.update_item import UpdateCatalogItemUseCase
from app.core.exceptions import NotFoundError
from app.core.tenant import CompanyContext
from app.domain.catalog.entities import CatalogItem
from app.domain.catalog.repository import CatalogItemRepository, StockMovementRepository
from app.domain.company.roles import CompanyRole
from app.domain.user.entities import User
from app.schemas.catalog import (
    AdjustStockRequest,
    CatalogItemResponse,
    CreateCatalogItemRequest,
    UpdateCatalogItemRequest,
)

router = APIRouter(prefix="/companies/{company_id}/catalog-items", tags=["catalog"])

_STAFF_ROLES = (
    CompanyRole.OWNER,
    CompanyRole.ADMIN,
    CompanyRole.MANAGER,
    CompanyRole.EMPLOYEE,
)
_MANAGEMENT_ROLES = (CompanyRole.OWNER, CompanyRole.ADMIN, CompanyRole.MANAGER)


def _to_response(item: CatalogItem) -> CatalogItemResponse:
    return CatalogItemResponse(
        id=item.id,
        company_id=item.company_id,
        name=item.name,
        description=item.description,
        price_cents=item.price_cents,
        kind=item.kind,
        tracks_inventory=item.tracks_inventory,
        stock_quantity=item.stock_quantity,
        is_active=item.is_active,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.post("", response_model=CatalogItemResponse, status_code=status.HTTP_201_CREATED)
async def create_catalog_item(
    payload: CreateCatalogItemRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_MANAGEMENT_ROLES))],
    item_repository: Annotated[CatalogItemRepository, Depends(get_catalog_item_repository)],
) -> CatalogItemResponse:
    use_case = CreateCatalogItemUseCase(item_repository)
    item = await use_case.execute(
        name=payload.name,
        description=payload.description,
        price_cents=payload.price_cents,
        kind=payload.kind,
        tracks_inventory=payload.tracks_inventory,
        stock_quantity=payload.stock_quantity,
    )
    return _to_response(item)


@router.get("", response_model=list[CatalogItemResponse])
async def list_catalog_items(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    item_repository: Annotated[CatalogItemRepository, Depends(get_catalog_item_repository)],
    only_active: Annotated[bool, Query()] = True,
) -> list[CatalogItemResponse]:
    items = await item_repository.list_all(only_active=only_active)
    return [_to_response(item) for item in items]


@router.get("/{item_id}", response_model=CatalogItemResponse)
async def get_catalog_item(
    item_id: str,
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    item_repository: Annotated[CatalogItemRepository, Depends(get_catalog_item_repository)],
) -> CatalogItemResponse:
    item = await item_repository.get_by_id(item_id)
    if item is None:
        raise NotFoundError("Item de catálogo não encontrado.")
    return _to_response(item)


@router.patch("/{item_id}", response_model=CatalogItemResponse)
async def update_catalog_item(
    item_id: str,
    payload: UpdateCatalogItemRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_MANAGEMENT_ROLES))],
    item_repository: Annotated[CatalogItemRepository, Depends(get_catalog_item_repository)],
) -> CatalogItemResponse:
    use_case = UpdateCatalogItemUseCase(item_repository)
    item = await use_case.execute(item_id=item_id, **payload.model_dump(exclude_unset=True))
    return _to_response(item)


@router.post("/{item_id}/adjust-stock", response_model=CatalogItemResponse)
async def adjust_stock(
    item_id: str,
    payload: AdjustStockRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_STAFF_ROLES))],
    current_user: Annotated[User, Depends(get_current_user)],
    item_repository: Annotated[CatalogItemRepository, Depends(get_catalog_item_repository)],
    movement_repository: Annotated[StockMovementRepository, Depends(get_stock_movement_repository)],
) -> CatalogItemResponse:
    use_case = AdjustStockUseCase(item_repository, movement_repository)
    item = await use_case.execute(
        item_id=item_id,
        delta=payload.delta,
        reason=payload.reason,
        created_by=current_user.id,
    )
    return _to_response(item)
