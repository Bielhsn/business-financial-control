import structlog

from app.core.audit import audit_event


def test_audit_event_emits_structured_log() -> None:
    with structlog.testing.capture_logs() as captured:
        audit_event(
            "transaction_created",
            user_id="user-1",
            company_id="company-1",
            amount_cents=1500,
        )

    assert len(captured) == 1
    event = captured[0]
    assert event["event"] == "audit_event"
    assert event["action"] == "transaction_created"
    assert event["user_id"] == "user-1"
    assert event["company_id"] == "company-1"
    assert event["amount_cents"] == 1500
