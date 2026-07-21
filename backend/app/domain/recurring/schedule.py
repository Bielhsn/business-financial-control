"""Cálculo puro da próxima data de uma recorrência.

Isolado e sem I/O para ser testável com valores primitivos. O `anchor_day`
preserva o dia do mês original: uma recorrência "todo dia 31" cai em 28/29/30
nos meses curtos, mas volta ao dia 31 quando o mês permite."""

import calendar
from datetime import datetime, timedelta

from app.domain.recurring.entities import RecurrenceFrequency


def next_occurrence(
    current: datetime, frequency: RecurrenceFrequency, *, anchor_day: int
) -> datetime:
    if frequency == RecurrenceFrequency.WEEKLY:
        return current + timedelta(days=7)
    if frequency == RecurrenceFrequency.MONTHLY:
        year = current.year + (1 if current.month == 12 else 0)
        month = 1 if current.month == 12 else current.month + 1
        day = min(anchor_day, calendar.monthrange(year, month)[1])
        return current.replace(year=year, month=month, day=day)
    if frequency == RecurrenceFrequency.YEARLY:
        year = current.year + 1
        day = min(anchor_day, calendar.monthrange(year, current.month)[1])
        return current.replace(year=year, day=day)
    raise ValueError(f"Periodicidade não suportada: {frequency}")
