from dataclasses import dataclass
from enum import StrEnum


class InsightKind(StrEnum):
    HIGHLIGHT = "highlight"
    WARNING = "warning"
    OPPORTUNITY = "opportunity"


@dataclass
class FinancialInsight:
    kind: InsightKind
    title: str
    message: str
