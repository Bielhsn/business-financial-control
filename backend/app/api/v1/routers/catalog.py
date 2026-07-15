from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import (
    get_audit_log_repository,
    get_catalog_item_repository,
    get_company_context,
    get_current_user,
    get_stock_movement_repository,
    require_role,
)
from app.application.catalog.adjust_stock import AdjustStockUseCase
from app.application.catalog.create_item import CreateCatalogItemUseCase
from app.application.catalog.update_item import UpdateCatalogItemUseCase
from app.core.audit import record_audit
from app.core.exceptions import NotFoundError
from app.core.tenant import CompanyContext
from app.domain.audit.repository import AuditLogRepository
from app.domain.catalog.entities import CatalogItem, ProductVariant
from app.domain.catalog.repository import CatalogItemRepository, StockMovementRepository
from app.domain.company.roles import CompanyRole
from app.domain.user.entities import User
from app.schemas.catalog import (
    AdjustStockRequest,
    CatalogItemResponse,
    CreateCatalogItemRequest,
    ProductVariantPayload,
    ProductVariantResponse,
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


def _to_variant_entity(payload: ProductVariantPayload) -> ProductVariant:
    return ProductVariant(
        name=payload.name,
        sku=payload.sku,
        barcode=payload.barcode,
        price_cents=payload.price_cents,
        promo_price_cents=payload.promo_price_cents,
        stock_quantity=payload.stock_quantity,
    )


def _to_response(item: CatalogItem) -> CatalogItemResponse:
    margin_cents: int | None = None
    margin_pct: float | None = None
    if item.cost_price_cents is not None:
        effective_price = item.promo_price_cents or item.price_cents
        margin_cents = effective_price - item.cost_price_cents
        if effective_price > 0:
            margin_pct = round(margin_cents / effective_price * 100, 2)
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
        sku=item.sku,
        barcode=item.barcode,
        brand=item.brand,
        supplier=item.supplier,
        category=item.category,
        subcategory=item.subcategory,
        short_description=item.short_description,
        tags=item.tags,
        cost_price_cents=item.cost_price_cents,
        promo_price_cents=item.promo_price_cents,
        min_stock=item.min_stock,
        max_stock=item.max_stock,
        stock_location=item.stock_location,
        images=item.images,
        variants=[
            ProductVariantResponse(
                name=variant.name,
                sku=variant.sku,
                barcode=variant.barcode,
                price_cents=variant.price_cents,
                promo_price_cents=variant.promo_price_cents,
                stock_quantity=variant.stock_quantity,
            )
            for variant in item.variants
        ],
        margin_cents=margin_cents,
        margin_pct=margin_pct,
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
        sku=payload.sku,
        barcode=payload.barcode,
        brand=payload.brand,
        supplier=payload.supplier,
        category=payload.category,
        subcategory=payload.subcategory,
        short_description=payload.short_description,
        tags=payload.tags,
        cost_price_cents=payload.cost_price_cents,
        promo_price_cents=payload.promo_price_cents,
        min_stock=payload.min_stock,
        max_stock=payload.max_stock,
        stock_location=payload.stock_location,
        images=payload.images,
        variants=[_to_variant_entity(variant) for variant in payload.variants],
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
    fields: dict[str, object] = payload.model_dump(exclude_unset=True)
    if payload.variants is not None:
        fields["variants"] = [_to_variant_entity(variant) for variant in payload.variants]
    item = await use_case.execute(item_id=item_id, **fields)
    return _to_response(item)


@router.post("/{item_id}/adjust-stock", response_model=CatalogItemResponse)
async def adjust_stock(
    item_id: str,
    payload: AdjustStockRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_STAFF_ROLES))],
    current_user: Annotated[User, Depends(get_current_user)],
    item_repository: Annotated[CatalogItemRepository, Depends(get_catalog_item_repository)],
    movement_repository: Annotated[StockMovementRepository, Depends(get_stock_movement_repository)],
    audit_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> CatalogItemResponse:
    use_case = AdjustStockUseCase(item_repository, movement_repository)
    item = await use_case.execute(
        item_id=item_id,
        delta=payload.delta,
        reason=payload.reason,
        created_by=current_user.id,
    )
    await record_audit(
        audit_repository,
        "stock_adjusted",
        user_id=current_user.id,
        company_id=company_context.company_id,
        item_id=item_id,
        delta=payload.delta,
    )
    return _to_response(item)
