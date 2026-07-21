from datetime import UTC, datetime
from typing import Any

from app.core.exceptions import UnauthorizedError
from app.core.tenant import get_current_company_id
from app.domain.admin.metrics import CompanySummary, ConnectionSummary, FinancialTotals
from app.domain.advisor.entities import BusinessSignal
from app.domain.apikey.entities import ApiKey
from app.domain.appointment.entities import Appointment, AppointmentStatus
from app.domain.audit.entities import AuditEntry
from app.domain.auth.entities import RefreshToken
from app.domain.auth.google import GoogleIdentity
from app.domain.auth.verification import VerificationCode, VerificationPurpose
from app.domain.blueprint.entities import (
    CompanyBlueprint,
    CustomFieldDefinition,
    KPIDefinition,
    SuggestedFinancialCategory,
)
from app.domain.blueprint.ports import CompanyBlueprintDraft
from app.domain.catalog.entities import (
    CatalogItem,
    CatalogItemKind,
    ProductVariant,
    StockMovement,
)
from app.domain.client.entities import Client
from app.domain.company.cnpj_lookup import CnpjInfo
from app.domain.company.entities import Company, CompanyMembership
from app.domain.company.invitation import Invitation, InvitationStatus
from app.domain.company.roles import CompanyRole
from app.domain.connector.entities import Connection, ConnectionStatus, NormalizedSale
from app.domain.dashboard.entities import DashboardSummary
from app.domain.dashboard.kpi_registry import KPIMetric
from app.domain.employee.entities import Employee
from app.domain.financial.entities import (
    FinancialCategory,
    FinancialCategoryType,
    FinancialTransaction,
    TransactionStatus,
)
from app.domain.goals.entities import FinancialGoal, GoalMetric
from app.domain.insights.entities import FinancialInsight, InsightKind
from app.domain.notifications.email import EmailMessage
from app.domain.platform_sales.entities import PlatformSale
from app.domain.recurring.entities import RecurrenceFrequency, RecurringTransaction
from app.domain.subscription.entities import BillingCycle, Subscription, SubscriptionStatus
from app.domain.subscription.plans import PlanTier
from app.domain.user.entities import User


class FakeUserRepository:
    def __init__(self) -> None:
        self._users_by_id: dict[str, User] = {}
        self._next_id = 1

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._users_by_id.values() if u.email == email), None)

    async def get_by_id(self, user_id: str) -> User | None:
        return self._users_by_id.get(user_id)

    async def create(
        self,
        *,
        email: str,
        hashed_password: str,
        full_name: str,
        is_verified: bool = True,
    ) -> User:
        user_id = str(self._next_id)
        self._next_id += 1
        now = datetime.now(UTC)
        user = User(
            id=user_id,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
            is_verified=is_verified,
            created_at=now,
            updated_at=now,
        )
        self._users_by_id[user_id] = user
        return user

    async def update(self, user_id: str, **fields: object) -> User | None:
        user = self._users_by_id.get(user_id)
        if user is None:
            return None
        for key, value in fields.items():
            setattr(user, key, value)
        user.updated_at = datetime.now(UTC)
        return user


class FakeRefreshTokenRepository:
    def __init__(self) -> None:
        self._tokens: dict[str, RefreshToken] = {}
        self._next_id = 1

    async def create(self, *, user_id: str, token_hash: str, expires_at: datetime) -> RefreshToken:
        token_id = str(self._next_id)
        self._next_id += 1
        token = RefreshToken(
            id=token_id,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked=False,
            created_at=datetime.now(UTC),
        )
        self._tokens[token_id] = token
        return token

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        return next((t for t in self._tokens.values() if t.token_hash == token_hash), None)

    async def revoke(self, refresh_token_id: str) -> None:
        token = self._tokens.get(refresh_token_id)
        if token is not None:
            token.revoked = True

    async def revoke_all_for_user(self, user_id: str) -> None:
        for token in self._tokens.values():
            if token.user_id == user_id:
                token.revoked = True


class FakePasswordHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, hashed_password: str) -> bool:
        return hashed_password == f"hashed:{password}"


class FakeTokenService:
    def __init__(self) -> None:
        self._counter = 0

    def create_access_token(self, subject: str) -> str:
        return f"access:{subject}"

    def decode_access_token(self, token: str) -> dict[str, Any]:
        if not token.startswith("access:"):
            raise UnauthorizedError("Token inválido ou expirado.")
        return {"sub": token.removeprefix("access:")}

    def generate_refresh_token(self) -> str:
        self._counter += 1
        return f"refresh-raw-{self._counter}"

    def hash_refresh_token(self, raw_token: str) -> str:
        return f"hash:{raw_token}"


class FakeCompanyRepository:
    def __init__(self) -> None:
        self._companies: dict[str, Company] = {}
        self._next_id = 1

    async def create(
        self,
        *,
        name: str,
        segment: str,
        employee_count: int,
        average_customer_count: int,
        city: str,
        state: str,
        country: str,
        size: str,
        tax_regime: str | None,
        additional_info: str | None,
        currency: str = "BRL",
        sales_channels: list[str] | None = None,
        sales_mode: str | None = None,
        main_offerings: str | None = None,
        legal_name: str | None = None,
        trade_name: str | None = None,
        cnpj: str | None = None,
        subsegment: str | None = None,
        monthly_revenue_cents: int | None = None,
        phone: str | None = None,
        email: str | None = None,
        website: str | None = None,
        social_links: dict[str, str] | None = None,
    ) -> Company:
        company_id = str(self._next_id)
        self._next_id += 1
        now = datetime.now(UTC)
        company = Company(
            id=company_id,
            name=name,
            segment=segment,
            employee_count=employee_count,
            average_customer_count=average_customer_count,
            city=city,
            state=state,
            country=country,
            size=size,
            tax_regime=tax_regime,
            additional_info=additional_info,
            currency=currency,
            sales_channels=sales_channels or [],
            sales_mode=sales_mode,
            main_offerings=main_offerings,
            legal_name=legal_name,
            trade_name=trade_name,
            cnpj=cnpj,
            subsegment=subsegment,
            monthly_revenue_cents=monthly_revenue_cents,
            phone=phone,
            email=email,
            website=website,
            social_links=social_links or {},
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self._companies[company_id] = company
        return company

    async def get_by_id(self, company_id: str) -> Company | None:
        return self._companies.get(company_id)

    async def update(self, company_id: str, **fields: object) -> Company | None:
        company = self._companies.get(company_id)
        if company is None:
            return None
        for key, value in fields.items():
            setattr(company, key, value)
        company.updated_at = datetime.now(UTC)
        return company

    async def delete(self, company_id: str) -> None:
        self._companies.pop(company_id, None)

    async def list_all_ids(self) -> list[str]:
        return list(self._companies.keys())


class FakeCompanyMembershipRepository:
    def __init__(self) -> None:
        self._memberships: dict[str, CompanyMembership] = {}
        self._next_id = 1
        self.fail_on_create = False

    async def create(
        self, *, company_id: str, user_id: str, role: CompanyRole
    ) -> CompanyMembership:
        if self.fail_on_create:
            raise RuntimeError("Falha simulada ao criar vínculo.")
        membership_id = str(self._next_id)
        self._next_id += 1
        membership = CompanyMembership(
            id=membership_id,
            company_id=company_id,
            user_id=user_id,
            role=role,
            created_at=datetime.now(UTC),
        )
        self._memberships[membership_id] = membership
        return membership

    async def get_by_user_and_company(
        self, user_id: str, company_id: str
    ) -> CompanyMembership | None:
        return next(
            (
                m
                for m in self._memberships.values()
                if m.user_id == user_id and m.company_id == company_id
            ),
            None,
        )

    async def list_for_user(self, user_id: str) -> list[CompanyMembership]:
        return [m for m in self._memberships.values() if m.user_id == user_id]

    async def list_for_company(self, company_id: str) -> list[CompanyMembership]:
        return [m for m in self._memberships.values() if m.company_id == company_id]

    async def update_role(self, membership_id: str, role: CompanyRole) -> CompanyMembership | None:
        membership = self._memberships.get(membership_id)
        if membership is None:
            return None
        membership.role = role
        return membership

    async def delete(self, membership_id: str) -> None:
        self._memberships.pop(membership_id, None)


class FakeCompanyBlueprintRepository:
    def __init__(self) -> None:
        self._blueprints: dict[str, CompanyBlueprint] = {}
        self._next_id = 1

    async def upsert(
        self,
        *,
        company_id: str,
        modules: list[str],
        financial_categories: list[SuggestedFinancialCategory],
        kpis: list[KPIDefinition],
        client_custom_fields: list[CustomFieldDefinition],
        ai_provider: str,
        integrations: list[str] | None = None,
    ) -> CompanyBlueprint:
        existing = self._blueprints.get(company_id)
        if existing is not None:
            blueprint_id = existing.id
        else:
            blueprint_id = str(self._next_id)
            self._next_id += 1

        blueprint = CompanyBlueprint(
            id=blueprint_id,
            company_id=company_id,
            modules=modules,
            financial_categories=financial_categories,
            kpis=kpis,
            client_custom_fields=client_custom_fields,
            ai_provider=ai_provider,
            generated_at=datetime.now(UTC),
            integrations=integrations or [],
        )
        self._blueprints[company_id] = blueprint
        return blueprint

    async def get_by_company_id(self, company_id: str) -> CompanyBlueprint | None:
        return self._blueprints.get(company_id)


class FakeAIProvider:
    def __init__(self, draft: CompanyBlueprintDraft | None = None) -> None:
        self._draft = draft or CompanyBlueprintDraft(
            modules=["financial_core", "clients"],
            financial_categories=[
                SuggestedFinancialCategory(name="Vendas", type=FinancialCategoryType.INCOME)
            ],
            kpis=[
                KPIDefinition(
                    key="average_ticket",
                    name="Ticket médio",
                    description="Valor médio por venda.",
                    metric=KPIMetric.AVERAGE_TICKET,
                )
            ],
            client_custom_fields=[],
            integrations=["whatsapp", "mercado_pago"],
        )
        self.calls: list[tuple[Company, str | None]] = []
        self.insight_calls: list[tuple[Company, DashboardSummary]] = []
        self.summary_calls: list[tuple[Company, DashboardSummary]] = []
        self.question_calls: list[tuple[Company, DashboardSummary, str]] = []
        self.recommendation_calls: list[tuple[Company, DashboardSummary, list[BusinessSignal]]] = []

    async def generate_company_blueprint(
        self, *, company: Company, additional_context: str | None
    ) -> CompanyBlueprintDraft:
        self.calls.append((company, additional_context))
        return self._draft

    async def generate_financial_insights(
        self, *, company: Company, summary: DashboardSummary
    ) -> list[FinancialInsight]:
        self.insight_calls.append((company, summary))
        return [
            FinancialInsight(
                kind=InsightKind.HIGHLIGHT,
                title="Lucro saudável",
                message="Sua margem está acima da média do segmento.",
            ),
            FinancialInsight(
                kind=InsightKind.WARNING,
                title="Despesas em alta",
                message="As despesas cresceram em relação ao período anterior.",
            ),
        ]

    async def generate_period_summary(self, *, company: Company, summary: DashboardSummary) -> str:
        self.summary_calls.append((company, summary))
        return "O período fechou com lucro sólido e despesas sob controle."

    async def answer_financial_question(
        self, *, company: Company, summary: DashboardSummary, question: str
    ) -> str:
        self.question_calls.append((company, summary, question))
        return f"Resposta baseada nos agregados para: {question}"

    async def generate_recommendations(
        self, *, company: Company, summary: DashboardSummary, signals: list[BusinessSignal]
    ) -> str:
        self.recommendation_calls.append((company, summary, signals))
        return "- **Reponha o estoque:** priorize os produtos zerados nesta semana."


class FakeFinancialCategoryRepository:
    def __init__(self) -> None:
        self._categories: dict[str, FinancialCategory] = {}
        self._next_id = 1

    async def create(self, *, name: str, type: FinancialCategoryType) -> FinancialCategory:
        category_id = str(self._next_id)
        self._next_id += 1
        category = FinancialCategory(
            id=category_id,
            company_id="company-1",
            name=name,
            type=type,
            is_active=True,
            created_at=datetime.now(UTC),
        )
        self._categories[category_id] = category
        return category

    async def get_by_id(self, category_id: str) -> FinancialCategory | None:
        return self._categories.get(category_id)

    async def get_by_name_and_type(
        self, name: str, type: FinancialCategoryType
    ) -> FinancialCategory | None:
        return next(
            (c for c in self._categories.values() if c.name == name and c.type == type), None
        )

    async def list_all(self, *, only_active: bool = True) -> list[FinancialCategory]:
        return [c for c in self._categories.values() if not only_active or c.is_active]

    async def update(self, category_id: str, **fields: object) -> FinancialCategory | None:
        category = self._categories.get(category_id)
        if category is None:
            return None
        for key, value in fields.items():
            setattr(category, key, value)
        return category


class FakeFinancialTransactionRepository:
    def __init__(self) -> None:
        self._transactions: dict[str, FinancialTransaction] = {}
        self._next_id = 1

    async def create(
        self,
        *,
        category_id: str,
        type: FinancialCategoryType,
        amount_cents: int,
        description: str,
        status: TransactionStatus,
        due_date: datetime | None,
        paid_at: datetime | None,
        notes: str | None,
        client_id: str | None = None,
        created_by: str,
        external_ref: str | None = None,
    ) -> FinancialTransaction:
        transaction_id = str(self._next_id)
        self._next_id += 1
        now = datetime.now(UTC)
        transaction = FinancialTransaction(
            id=transaction_id,
            company_id="company-1",
            category_id=category_id,
            type=type,
            amount_cents=amount_cents,
            description=description,
            status=status,
            due_date=due_date,
            paid_at=paid_at,
            notes=notes,
            client_id=client_id,
            created_by=created_by,
            created_at=now,
            updated_at=now,
            external_ref=external_ref,
        )
        self._transactions[transaction_id] = transaction
        return transaction

    async def get_by_id(self, transaction_id: str) -> FinancialTransaction | None:
        return self._transactions.get(transaction_id)

    async def find_by_external_ref(self, external_ref: str) -> FinancialTransaction | None:
        for transaction in self._transactions.values():
            if transaction.external_ref == external_ref:
                return transaction
        return None

    async def list_paid_for_client(self, client_id: str) -> list[FinancialTransaction]:
        return [
            t
            for t in self._transactions.values()
            if t.client_id == client_id and t.status == TransactionStatus.PAID
        ]

    async def list_all(
        self,
        *,
        type: FinancialCategoryType | None = None,
        status: TransactionStatus | None = None,
    ) -> list[FinancialTransaction]:
        results = list(self._transactions.values())
        if type is not None:
            results = [t for t in results if t.type == type]
        if status is not None:
            results = [t for t in results if t.status == status]
        return results

    async def update(self, transaction_id: str, **fields: object) -> FinancialTransaction | None:
        transaction = self._transactions.get(transaction_id)
        if transaction is None:
            return None
        for key, value in fields.items():
            setattr(transaction, key, value)
        return transaction

    async def sum_paid_between(
        self, *, type: FinancialCategoryType, start: datetime, end: datetime
    ) -> int:
        return sum(
            t.amount_cents
            for t in self._transactions.values()
            if t.type == type
            and t.status == TransactionStatus.PAID
            and t.paid_at is not None
            and start <= t.paid_at <= end
        )

    async def list_paid_between(
        self, *, start: datetime, end: datetime
    ) -> list[FinancialTransaction]:
        return [
            t
            for t in self._transactions.values()
            if t.status == TransactionStatus.PAID
            and t.paid_at is not None
            and start <= t.paid_at <= end
        ]


class FakeClientRepository:
    def __init__(self) -> None:
        self._clients: dict[str, Client] = {}
        self._next_id = 1

    async def create(
        self,
        *,
        name: str,
        email: str | None,
        phone: str | None,
        notes: str | None,
        custom_fields: dict[str, str],
    ) -> Client:
        client_id = str(self._next_id)
        self._next_id += 1
        now = datetime.now(UTC)
        client = Client(
            id=client_id,
            company_id="company-1",
            name=name,
            email=email,
            phone=phone,
            notes=notes,
            custom_fields=custom_fields,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self._clients[client_id] = client
        return client

    async def get_by_id(self, client_id: str) -> Client | None:
        return self._clients.get(client_id)

    async def list_all(self, *, only_active: bool = True) -> list[Client]:
        return [c for c in self._clients.values() if not only_active or c.is_active]

    async def update(self, client_id: str, **fields: object) -> Client | None:
        client = self._clients.get(client_id)
        if client is None:
            return None
        for key, value in fields.items():
            setattr(client, key, value)
        return client


class FakeCatalogItemRepository:
    def __init__(self) -> None:
        self._items: dict[str, CatalogItem] = {}
        self._next_id = 1

    async def create(
        self,
        *,
        name: str,
        description: str | None,
        price_cents: int,
        kind: CatalogItemKind,
        tracks_inventory: bool,
        stock_quantity: int | None,
        sku: str | None = None,
        barcode: str | None = None,
        brand: str | None = None,
        supplier: str | None = None,
        category: str | None = None,
        subcategory: str | None = None,
        short_description: str | None = None,
        tags: list[str] | None = None,
        cost_price_cents: int | None = None,
        promo_price_cents: int | None = None,
        min_stock: int | None = None,
        max_stock: int | None = None,
        stock_location: str | None = None,
        images: list[str] | None = None,
        variants: list[ProductVariant] | None = None,
    ) -> CatalogItem:
        item_id = str(self._next_id)
        self._next_id += 1
        now = datetime.now(UTC)
        item = CatalogItem(
            id=item_id,
            company_id="company-1",
            name=name,
            description=description,
            price_cents=price_cents,
            kind=kind,
            tracks_inventory=tracks_inventory,
            stock_quantity=stock_quantity,
            is_active=True,
            created_at=now,
            updated_at=now,
            sku=sku,
            barcode=barcode,
            brand=brand,
            supplier=supplier,
            category=category,
            subcategory=subcategory,
            short_description=short_description,
            tags=tags or [],
            cost_price_cents=cost_price_cents,
            promo_price_cents=promo_price_cents,
            min_stock=min_stock,
            max_stock=max_stock,
            stock_location=stock_location,
            images=images or [],
            variants=variants or [],
        )
        self._items[item_id] = item
        return item

    async def get_by_id(self, item_id: str) -> CatalogItem | None:
        return self._items.get(item_id)

    async def find_by_sku(self, sku: str) -> CatalogItem | None:
        for item in self._items.values():
            if item.sku == sku:
                return item
        return None

    async def list_all(self, *, only_active: bool = True) -> list[CatalogItem]:
        return [i for i in self._items.values() if not only_active or i.is_active]

    async def update(self, item_id: str, **fields: object) -> CatalogItem | None:
        item = self._items.get(item_id)
        if item is None:
            return None
        for key, value in fields.items():
            setattr(item, key, value)
        return item

    async def adjust_stock(self, item_id: str, *, delta: int) -> CatalogItem | None:
        item = self._items.get(item_id)
        if item is None:
            return None
        item.stock_quantity = (item.stock_quantity or 0) + delta
        return item


class FakeStockMovementRepository:
    def __init__(self) -> None:
        self._movements: dict[str, StockMovement] = {}
        self._next_id = 1

    async def create(
        self, *, item_id: str, delta: int, reason: str, created_by: str
    ) -> StockMovement:
        movement_id = str(self._next_id)
        self._next_id += 1
        movement = StockMovement(
            id=movement_id,
            company_id="company-1",
            item_id=item_id,
            delta=delta,
            reason=reason,
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        self._movements[movement_id] = movement
        return movement

    async def list_for_item(self, item_id: str) -> list[StockMovement]:
        return [m for m in self._movements.values() if m.item_id == item_id]


class FakeEmployeeRepository:
    def __init__(self) -> None:
        self._employees: dict[str, Employee] = {}
        self._next_id = 1

    async def create(
        self, *, name: str, email: str | None, phone: str | None, role_title: str | None
    ) -> Employee:
        employee_id = str(self._next_id)
        self._next_id += 1
        now = datetime.now(UTC)
        employee = Employee(
            id=employee_id,
            company_id="company-1",
            name=name,
            email=email,
            phone=phone,
            role_title=role_title,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self._employees[employee_id] = employee
        return employee

    async def get_by_id(self, employee_id: str) -> Employee | None:
        return self._employees.get(employee_id)

    async def list_all(self, *, only_active: bool = True) -> list[Employee]:
        return [e for e in self._employees.values() if not only_active or e.is_active]

    async def update(self, employee_id: str, **fields: object) -> Employee | None:
        employee = self._employees.get(employee_id)
        if employee is None:
            return None
        for key, value in fields.items():
            setattr(employee, key, value)
        return employee


class FakeAuditLogRepository:
    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []
        self._next_id = 1

    async def create(
        self,
        *,
        company_id: str,
        user_id: str | None,
        action: str,
        details: dict[str, object],
    ) -> AuditEntry:
        entry = AuditEntry(
            id=str(self._next_id),
            company_id=company_id,
            user_id=user_id,
            action=action,
            details=details,
            created_at=datetime.now(UTC),
        )
        self._next_id += 1
        self.entries.append(entry)
        return entry

    async def list_for_company(self, company_id: str, *, limit: int = 50) -> list[AuditEntry]:
        matching = [e for e in self.entries if e.company_id == company_id]
        matching.sort(key=lambda e: e.created_at or datetime.now(UTC), reverse=True)
        return matching[:limit]


class FakeAppointmentRepository:
    def __init__(self) -> None:
        self._appointments: dict[str, Appointment] = {}
        self._next_id = 1

    async def create(
        self,
        *,
        title: str,
        starts_at: datetime,
        duration_minutes: int,
        client_id: str | None,
        client_name: str | None,
        employee_id: str | None,
        employee_name: str | None,
        catalog_item_id: str | None,
        price_cents: int | None,
        notes: str | None,
        created_by: str,
    ) -> Appointment:
        appointment_id = str(self._next_id)
        self._next_id += 1
        now = datetime.now(UTC)
        appointment = Appointment(
            id=appointment_id,
            company_id="company-1",
            title=title,
            starts_at=starts_at,
            duration_minutes=duration_minutes,
            status=AppointmentStatus.SCHEDULED,
            client_id=client_id,
            client_name=client_name,
            employee_id=employee_id,
            employee_name=employee_name,
            catalog_item_id=catalog_item_id,
            price_cents=price_cents,
            notes=notes,
            revenue_transaction_id=None,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        self._appointments[appointment_id] = appointment
        return appointment

    async def get_by_id(self, appointment_id: str) -> Appointment | None:
        return self._appointments.get(appointment_id)

    async def list_between(
        self,
        *,
        start: datetime,
        end: datetime,
        employee_id: str | None = None,
    ) -> list[Appointment]:
        result = [
            a
            for a in self._appointments.values()
            if start <= a.starts_at < end and (employee_id is None or a.employee_id == employee_id)
        ]
        result.sort(key=lambda a: a.starts_at)
        return result

    async def update(self, appointment_id: str, **fields: object) -> Appointment | None:
        appointment = self._appointments.get(appointment_id)
        if appointment is None:
            return None
        for key, value in fields.items():
            if key == "status" and isinstance(value, str):
                value = AppointmentStatus(value)
            setattr(appointment, key, value)
        return appointment


class FakeSecretCipher:
    """Cifra reversível trivial para testes (não é segura — só inverte a string)."""

    def encrypt(self, plaintext: str) -> str:
        return "enc:" + plaintext

    def decrypt(self, token: str) -> str:
        return token.removeprefix("enc:")


class FakeConnectionRepository:
    def __init__(self) -> None:
        self._connections: dict[str, Connection] = {}
        self._secrets: dict[str, str] = {}
        self._next_id = 1

    async def upsert(
        self, *, provider: str, encrypted_secrets: str, config: dict[str, str]
    ) -> Connection:
        now = datetime.now(UTC)
        self._secrets[provider] = encrypted_secrets
        existing = self._connections.get(provider)
        if existing is None:
            connection = Connection(
                id=str(self._next_id),
                company_id="company-1",
                provider=provider,
                status=ConnectionStatus.CONNECTED,
                config=dict(config),
                last_synced_at=None,
                last_error=None,
                created_at=now,
                updated_at=now,
            )
            self._next_id += 1
        else:
            connection = existing
            connection.config = dict(config)
            connection.status = ConnectionStatus.CONNECTED
            connection.last_error = None
            connection.updated_at = now
        self._connections[provider] = connection
        return connection

    async def get_by_provider(self, provider: str) -> Connection | None:
        return self._connections.get(provider)

    async def get_encrypted_secrets(self, provider: str) -> str | None:
        return self._secrets.get(provider)

    async def list_all(self) -> list[Connection]:
        return list(self._connections.values())

    async def mark_synced(self, provider: str) -> None:
        connection = self._connections.get(provider)
        if connection is not None:
            connection.last_synced_at = datetime.now(UTC)
            connection.status = ConnectionStatus.CONNECTED
            connection.last_error = None

    async def mark_status(
        self, provider: str, *, status: ConnectionStatus, error: str | None
    ) -> None:
        connection = self._connections.get(provider)
        if connection is not None:
            connection.status = status
            connection.last_error = error

    async def delete(self, provider: str) -> bool:
        if provider in self._connections:
            del self._connections[provider]
            self._secrets.pop(provider, None)
            return True
        return False


class FakeConnector:
    """Conector fake configurável para testes de aplicação/API (sem rede)."""

    provider = "hotmart"

    def __init__(self, sales: list[NormalizedSale] | None = None) -> None:
        self._sales = sales or []
        self.test_calls: list[dict[str, str]] = []
        self.fetch_calls: list[dict[str, str]] = []

    async def test_connection(self, credentials: dict[str, str]) -> None:
        self.test_calls.append(credentials)

    async def fetch_sales(
        self, credentials: dict[str, str], *, since: object = None
    ) -> list[NormalizedSale]:
        self.fetch_calls.append(credentials)
        return self._sales


class FakeCnpjLookup:
    """Consulta de CNPJ fake para testes de API (sem rede)."""

    def __init__(self, info: CnpjInfo | None = None) -> None:
        self._info = info
        self.calls: list[str] = []

    async def fetch(self, cnpj: str) -> CnpjInfo:
        self.calls.append(cnpj)
        if self._info is not None:
            return self._info
        return CnpjInfo(
            cnpj=cnpj,
            legal_name="Empresa Exemplo LTDA",
            trade_name="Exemplo",
            status="ATIVA",
            is_active=True,
            city="São Paulo",
            state="SP",
            email="contato@exemplo.com",
            phone="1133224455",
            main_activity="Desenvolvimento de software",
        )


class FakeVerificationCodeRepository:
    def __init__(self) -> None:
        self._codes: dict[str, VerificationCode] = {}
        self._next_id = 1

    async def create(
        self,
        *,
        user_id: str,
        purpose: VerificationPurpose,
        code_hash: str,
        expires_at: datetime,
    ) -> VerificationCode:
        code_id = str(self._next_id)
        self._next_id += 1
        code = VerificationCode(
            id=code_id,
            user_id=user_id,
            purpose=purpose,
            code_hash=code_hash,
            expires_at=expires_at,
            used=False,
            created_at=datetime.now(UTC),
        )
        self._codes[code_id] = code
        return code

    async def get_active(
        self, *, user_id: str, purpose: VerificationPurpose, code_hash: str
    ) -> VerificationCode | None:
        for code in self._codes.values():
            if (
                code.user_id == user_id
                and code.purpose == purpose
                and code.code_hash == code_hash
                and not code.used
                and code.expires_at >= datetime.now(UTC)
            ):
                return code
        return None

    async def mark_used(self, code_id: str) -> None:
        code = self._codes.get(code_id)
        if code is not None:
            code.used = True

    async def invalidate_for(self, *, user_id: str, purpose: VerificationPurpose) -> None:
        for code in self._codes.values():
            if code.user_id == user_id and code.purpose == purpose:
                code.used = True


class FakeEmailSender:
    def __init__(self) -> None:
        self.sent: list[EmailMessage] = []

    async def send(self, message: EmailMessage) -> None:
        self.sent.append(message)


class FakeGoogleTokenVerifier:
    """Mapeia id_token -> identidade (configurável); token desconhecido = inválido."""

    def __init__(self, identities: dict[str, GoogleIdentity] | None = None) -> None:
        self._identities = identities or {}

    def register(self, id_token: str, identity: GoogleIdentity) -> None:
        self._identities[id_token] = identity

    async def verify(self, id_token: str) -> GoogleIdentity:
        identity = self._identities.get(id_token)
        if identity is None:
            raise UnauthorizedError("Token do Google inválido ou expirado.")
        return identity


class FakeInvitationRepository:
    def __init__(self) -> None:
        self._invitations: dict[str, Invitation] = {}
        self._next_id = 1

    async def create(
        self,
        *,
        company_id: str,
        email: str,
        role: CompanyRole,
        token: str,
        invited_by: str,
        expires_at: datetime,
    ) -> Invitation:
        invitation_id = str(self._next_id)
        self._next_id += 1
        invitation = Invitation(
            id=invitation_id,
            company_id=company_id,
            email=email,
            role=role,
            token=token,
            status=InvitationStatus.PENDING,
            invited_by=invited_by,
            expires_at=expires_at,
            created_at=datetime.now(UTC),
        )
        self._invitations[invitation_id] = invitation
        return invitation

    async def list_pending_for_company(self, company_id: str) -> list[Invitation]:
        return [
            i
            for i in self._invitations.values()
            if i.company_id == company_id and i.status == InvitationStatus.PENDING
        ]

    async def get_by_token(self, token: str) -> Invitation | None:
        return next((i for i in self._invitations.values() if i.token == token), None)

    async def get_pending_for_email(self, *, company_id: str, email: str) -> Invitation | None:
        return next(
            (
                i
                for i in self._invitations.values()
                if i.company_id == company_id
                and i.email == email
                and i.status == InvitationStatus.PENDING
            ),
            None,
        )

    async def mark_accepted(self, invitation_id: str) -> None:
        invitation = self._invitations.get(invitation_id)
        if invitation is not None:
            invitation.status = InvitationStatus.ACCEPTED

    async def mark_revoked(self, invitation_id: str) -> None:
        invitation = self._invitations.get(invitation_id)
        if invitation is not None:
            invitation.status = InvitationStatus.REVOKED


class FakeCompanyDataService:
    """Exporter + eraser em memória para testes (registra a empresa apagada)."""

    def __init__(self) -> None:
        self.erased: list[str] = []

    async def export(self, company_id: str) -> dict[str, object]:
        return {"company": {"id": company_id}, "financial_transactions": []}

    async def erase(self, company_id: str) -> None:
        self.erased.append(company_id)


class FakeSubscriptionRepository:
    def __init__(self) -> None:
        self._subscriptions: dict[str, Subscription] = {}
        self._next_id = 1

    async def get_by_company(self, company_id: str) -> Subscription | None:
        return self._subscriptions.get(company_id)

    async def upsert(
        self,
        *,
        company_id: str,
        tier: PlanTier,
        status: SubscriptionStatus,
        billing_cycle: BillingCycle,
        trial_ends_at: datetime | None,
        current_period_end: datetime | None,
        cancel_at_period_end: bool,
    ) -> Subscription:
        now = datetime.now(UTC)
        existing = self._subscriptions.get(company_id)
        if existing is None:
            subscription_id = str(self._next_id)
            self._next_id += 1
            subscription = Subscription(
                id=subscription_id,
                company_id=company_id,
                tier=tier,
                status=status,
                billing_cycle=billing_cycle,
                started_at=now,
                updated_at=now,
                trial_ends_at=trial_ends_at,
                current_period_end=current_period_end,
                cancel_at_period_end=cancel_at_period_end,
            )
        else:
            subscription = Subscription(
                id=existing.id,
                company_id=company_id,
                tier=tier,
                status=status,
                billing_cycle=billing_cycle,
                started_at=existing.started_at,
                updated_at=now,
                trial_ends_at=trial_ends_at,
                current_period_end=current_period_end,
                cancel_at_period_end=cancel_at_period_end,
            )
        self._subscriptions[company_id] = subscription
        return subscription

    async def list_all(self) -> list[Subscription]:
        return list(self._subscriptions.values())


class FakeApiKeyRepository:
    def __init__(self) -> None:
        self._keys: dict[str, ApiKey] = {}
        self._by_hash: dict[str, str] = {}
        self._next_id = 1

    async def create(self, *, name: str, prefix: str, hashed_key: str) -> ApiKey:
        key_id = str(self._next_id)
        self._next_id += 1
        try:
            company_id = get_current_company_id()
        except RuntimeError:
            company_id = "company-1"
        key = ApiKey(
            id=key_id,
            company_id=company_id,
            name=name,
            prefix=prefix,
            created_at=datetime.now(UTC),
            last_used_at=None,
            revoked=False,
        )
        self._keys[key_id] = key
        self._by_hash[hashed_key] = key_id
        return key

    async def list_for_company(self) -> list[ApiKey]:
        return list(self._keys.values())

    async def get_active_by_hash(self, hashed_key: str) -> ApiKey | None:
        key_id = self._by_hash.get(hashed_key)
        if key_id is None:
            return None
        key = self._keys.get(key_id)
        return key if key and not key.revoked else None

    async def revoke(self, key_id: str) -> bool:
        key = self._keys.get(key_id)
        if key is None:
            return False
        key.revoked = True
        return True

    async def touch_last_used(self, key_id: str) -> None:
        key = self._keys.get(key_id)
        if key is not None:
            key.last_used_at = datetime.now(UTC)


class FakeGoalRepository:
    def __init__(self) -> None:
        self._goals: dict[GoalMetric, FinancialGoal] = {}
        self._next_id = 1

    async def list_all(self) -> list[FinancialGoal]:
        return list(self._goals.values())

    async def set(self, *, metric: GoalMetric, target_cents: int) -> FinancialGoal:
        existing = self._goals.get(metric)
        goal = FinancialGoal(
            id=existing.id if existing else str(self._next_id),
            company_id="company-1",
            metric=metric,
            target_cents=target_cents,
            updated_at=datetime.now(UTC),
        )
        if existing is None:
            self._next_id += 1
        self._goals[metric] = goal
        return goal

    async def delete(self, metric: GoalMetric) -> bool:
        return self._goals.pop(metric, None) is not None


class FakePlatformSaleRepository:
    def __init__(self) -> None:
        self._sales: dict[tuple[str, str], PlatformSale] = {}
        self._next_id = 1

    async def upsert(
        self,
        *,
        provider: str,
        external_id: str,
        product: str,
        amount_cents: int,
        occurred_at: datetime,
        is_refund: bool,
        buyer_name: str | None,
        buyer_email: str | None,
    ) -> bool:
        key = (provider, external_id)
        if key in self._sales:
            return False
        sale = PlatformSale(
            id=str(self._next_id),
            company_id="company-1",
            provider=provider,
            external_id=external_id,
            product=product,
            amount_cents=amount_cents,
            occurred_at=occurred_at,
            is_refund=is_refund,
            buyer_name=buyer_name,
            buyer_email=buyer_email,
            created_at=datetime.now(UTC),
        )
        self._sales[key] = sale
        self._next_id += 1
        return True

    async def list_since(self, since: datetime | None) -> list[PlatformSale]:
        sales = list(self._sales.values())
        if since is None:
            return sales
        return [s for s in sales if _as_aware(s.occurred_at) >= since]


def _as_aware(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


class FakeAdminMetricsRepository:
    """Métricas cross-tenant em memória — seeds ajustáveis pelos testes."""

    def __init__(self) -> None:
        self.companies: list[CompanySummary] = []
        self.users = 0
        self.connections: list[ConnectionSummary] = []
        self.income_cents = 0
        self.expense_cents = 0

    async def list_companies(self) -> list[CompanySummary]:
        return list(self.companies)

    async def count_users(self) -> int:
        return self.users

    async def list_connections(self) -> list[ConnectionSummary]:
        return list(self.connections)

    async def financial_totals(self) -> FinancialTotals:
        return FinancialTotals(income_cents=self.income_cents, expense_cents=self.expense_cents)


class FakeRecurringTransactionRepository:
    """Recorrências em memória, escopadas pela empresa do contexto atual."""

    def __init__(self, items: list[RecurringTransaction] | None = None) -> None:
        self._items: dict[str, RecurringTransaction] = {i.id: i for i in (items or [])}
        self._next_id = len(self._items) + 1

    def _scoped(self, items: list[RecurringTransaction]) -> list[RecurringTransaction]:
        # Filtra pela empresa do contexto quando há um; sem contexto (testes de
        # unidade do gerador) devolve tudo.
        try:
            company_id = get_current_company_id()
        except Exception:
            return items
        return [item for item in items if item.company_id == company_id]

    async def list_all(self) -> list[RecurringTransaction]:
        return self._scoped(list(self._items.values()))

    async def get_by_id(self, recurring_id: str) -> RecurringTransaction | None:
        return self._items.get(recurring_id)

    async def create(
        self,
        *,
        category_id: str,
        type: FinancialCategoryType,
        amount_cents: int,
        description: str,
        frequency: RecurrenceFrequency,
        anchor_day: int,
        next_run_date: datetime,
        notes: str | None,
        client_id: str | None,
        created_by: str,
    ) -> RecurringTransaction:
        now = datetime.now(UTC)
        recurring_id = str(self._next_id)
        self._next_id += 1
        try:
            company_id = get_current_company_id()
        except Exception:
            company_id = "company-1"
        item = RecurringTransaction(
            id=recurring_id,
            company_id=company_id,
            category_id=category_id,
            type=type,
            amount_cents=amount_cents,
            description=description,
            frequency=frequency,
            anchor_day=anchor_day,
            next_run_date=next_run_date,
            active=True,
            notes=notes,
            client_id=client_id,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        self._items[recurring_id] = item
        return item

    async def update(self, recurring_id: str, **fields: object) -> RecurringTransaction | None:
        item = self._items.get(recurring_id)
        if item is None:
            return None
        for name, value in fields.items():
            setattr(item, name, value)
        item.updated_at = datetime.now(UTC)
        return item

    async def delete(self, recurring_id: str) -> bool:
        return self._items.pop(recurring_id, None) is not None

    async def list_due(self, as_of: datetime) -> list[RecurringTransaction]:
        due = [i for i in self._items.values() if i.active and i.next_run_date <= as_of]
        return self._scoped(due)
