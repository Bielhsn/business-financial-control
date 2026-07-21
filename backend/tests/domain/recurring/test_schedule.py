from datetime import UTC, datetime

from app.domain.recurring.entities import RecurrenceFrequency
from app.domain.recurring.schedule import next_occurrence


def test_weekly_adds_seven_days() -> None:
    result = next_occurrence(
        datetime(2026, 7, 1, 9, 0, tzinfo=UTC), RecurrenceFrequency.WEEKLY, anchor_day=1
    )
    assert result == datetime(2026, 7, 8, 9, 0, tzinfo=UTC)


def test_monthly_advances_one_month_keeping_day_and_time() -> None:
    result = next_occurrence(
        datetime(2026, 3, 5, 8, 30, tzinfo=UTC), RecurrenceFrequency.MONTHLY, anchor_day=5
    )
    assert result == datetime(2026, 4, 5, 8, 30, tzinfo=UTC)


def test_monthly_clamps_to_last_day_of_short_month() -> None:
    # Dia 31 em janeiro → fevereiro só tem 28 (2026 não é bissexto).
    result = next_occurrence(
        datetime(2026, 1, 31, 12, 0, tzinfo=UTC), RecurrenceFrequency.MONTHLY, anchor_day=31
    )
    assert result == datetime(2026, 2, 28, 12, 0, tzinfo=UTC)


def test_monthly_returns_to_anchor_day_after_short_month() -> None:
    # Estava em 28/fev por causa do clamp, mas o anchor 31 volta em março.
    result = next_occurrence(
        datetime(2026, 2, 28, 12, 0, tzinfo=UTC), RecurrenceFrequency.MONTHLY, anchor_day=31
    )
    assert result == datetime(2026, 3, 31, 12, 0, tzinfo=UTC)


def test_monthly_december_rolls_into_next_year() -> None:
    result = next_occurrence(
        datetime(2026, 12, 10, 0, 0, tzinfo=UTC), RecurrenceFrequency.MONTHLY, anchor_day=10
    )
    assert result == datetime(2027, 1, 10, 0, 0, tzinfo=UTC)


def test_yearly_handles_leap_day() -> None:
    # 29/fev/2028 (bissexto) → 2029 não é bissexto, clampa para 28.
    result = next_occurrence(
        datetime(2028, 2, 29, 0, 0, tzinfo=UTC), RecurrenceFrequency.YEARLY, anchor_day=29
    )
    assert result == datetime(2029, 2, 28, 0, 0, tzinfo=UTC)
