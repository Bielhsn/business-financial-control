from datetime import UTC, datetime
from typing import Any

from app.core.exceptions import UnauthorizedError
from app.domain.auth.entities import RefreshToken
from app.domain.blueprint.entities import (
    CompanyBlueprint,
    CustomFieldDefinition,
    KPIDefinition,
    SuggestedFinancialCategory,
)
from app.domain.blueprint.ports import CompanyBlueprintDraft
from app.domain.catalog.entities import CatalogItem, CatalogItemKind, StockMovement
from app.domain.client.entities import Client
from app.domain.company.entities import Company, CompanyMembership
from app.domain.company.roles import CompanyRole
from app.domain.dashboard.entities import DashboardSummary
from app.domain.dashboard.kpi_registry import KPIMetric
from app.domain.employee.entities import Employee
from app.domain.financial.entities import (
    FinancialCategory,
    FinancialCategoryType,
    FinancialTransaction,
    TransactionStatus,
)
from app.domain.insights.entities import FinancialInsight, InsightKind
from app.domain.user.entities import User


class FakeUserRepository:
    def __init__(self) -> None:
        self._users_by_id: dict[str, User] = {}
        self._next_id = 1

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._users_by_id.values() if u.email == email), None)

    async def get_by_id(self, user_id: str) -> User | None:
        return self._users_by_id.get(user_id)

    async def create(self, *, email: str, hashed_password: str, full_name: str) -> User:
        user_id = str(self._next_id)
        self._next_id += 1
        now = datetime.now(UTC)
        user = User(
            id=user_id,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self._users_by_id[user_id] = user
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
        )
        self.calls: list[tuple[Company, str | None]] = []
        self.insight_calls: list[tuple[Company, DashboardSummary]] = []

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
        )
        self._transactions[transaction_id] = transaction
        return transaction

    async def get_by_id(self, transaction_id: str) -> FinancialTransaction | None:
        return self._transactions.get(transaction_id)

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
        )
        self._items[item_id] = item
        return item

    async def get_by_id(self, item_id: str) -> CatalogItem | None:
        return self._items.get(item_id)

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
