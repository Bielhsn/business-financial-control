from dataclasses import dataclass, field
from enum import StrEnum


class HealthRating(StrEnum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ATTENTION = "attention"
    CRITICAL = "critical"


@dataclass(frozen=True)
class HealthFactor:
    """Um componente do índice, com seu score (0..100) e peso. `detail` explica
    o número para o usuário — o índice nunca é uma caixa preta."""

    key: str
    label: str
    score: int  # 0..100
    weight: int
    detail: str


@dataclass(frozen=True)
class HealthScore:
    score: int  # 0..100 (média ponderada dos fatores disponíveis)
    rating: HealthRating
    factors: list[HealthFactor] = field(default_factory=list)
