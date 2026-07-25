from pydantic import BaseModel

from app.domain.segment.profile import SegmentProfile


class CatalogFieldPolicyResponse(BaseModel):
    sku: bool
    barcode: bool
    brand: bool
    supplier: bool
    variants: bool
    inventory: bool
    duration: bool


class SegmentTerminologyResponse(BaseModel):
    clients: str
    client_singular: str
    catalog: str
    products: str
    services: str
    employees: str
    employee_singular: str
    agenda: str
    appointment_singular: str
    transactions: str


class SegmentProfileResponse(BaseModel):
    """Contrato que o frontend usa para se adaptar ao negócio: rótulos, módulos,
    campos aplicáveis, exemplos e indicadores relevantes."""

    id: str
    label: str
    offering: str
    modules: list[str]
    terminology: SegmentTerminologyResponse
    catalog_fields: CatalogFieldPolicyResponse
    service_examples: list[str]
    product_examples: list[str]
    catalog_categories: list[str]
    income_categories: list[str]
    expense_categories: list[str]
    kpis: list[str]
    integrations: list[str]
    sells_products: bool
    sells_services: bool


def to_segment_profile_response(profile: SegmentProfile) -> SegmentProfileResponse:
    return SegmentProfileResponse(
        id=profile.id,
        label=profile.label,
        offering=profile.offering.value,
        modules=list(profile.modules),
        terminology=SegmentTerminologyResponse(
            clients=profile.terminology.clients,
            client_singular=profile.terminology.client_singular,
            catalog=profile.terminology.catalog,
            products=profile.terminology.products,
            services=profile.terminology.services,
            employees=profile.terminology.employees,
            employee_singular=profile.terminology.employee_singular,
            agenda=profile.terminology.agenda,
            appointment_singular=profile.terminology.appointment_singular,
            transactions=profile.terminology.transactions,
        ),
        catalog_fields=CatalogFieldPolicyResponse(
            sku=profile.catalog_fields.sku,
            barcode=profile.catalog_fields.barcode,
            brand=profile.catalog_fields.brand,
            supplier=profile.catalog_fields.supplier,
            variants=profile.catalog_fields.variants,
            inventory=profile.catalog_fields.inventory,
            duration=profile.catalog_fields.duration,
        ),
        service_examples=list(profile.service_examples),
        product_examples=list(profile.product_examples),
        catalog_categories=list(profile.catalog_categories),
        income_categories=list(profile.income_categories),
        expense_categories=list(profile.expense_categories),
        kpis=[metric.value for metric in profile.kpis],
        integrations=list(profile.integrations),
        sells_products=profile.sells_products,
        sells_services=profile.sells_services,
    )
