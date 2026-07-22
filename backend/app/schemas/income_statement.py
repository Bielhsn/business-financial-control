from pydantic import BaseModel


class StatementLineResponse(BaseModel):
    category_id: str
    category_name: str
    amount_cents: int


class IncomeStatementResponse(BaseModel):
    income_lines: list[StatementLineResponse]
    expense_lines: list[StatementLineResponse]
    total_income_cents: int
    total_expense_cents: int
    net_result_cents: int


class IncomeStatementComparisonResponse(BaseModel):
    year: int
    month: int
    current: IncomeStatementResponse
    previous_income_cents: int
    previous_expense_cents: int
    previous_net_result_cents: int
    income_change_pct: float | None
    expense_change_pct: float | None
    net_change_pct: float | None
