import pytest

from app.core import tenant


@pytest.fixture(autouse=True)
def _reset_tenant_context() -> None:
    token = tenant._current_company_id.set(None)
    yield
    tenant._current_company_id.reset(token)


def test_get_current_company_id_raises_when_not_set() -> None:
    with pytest.raises(RuntimeError):
        tenant.get_current_company_id()


def test_set_and_get_current_company_id() -> None:
    tenant.set_current_company_id("company-1")

    assert tenant.get_current_company_id() == "company-1"
