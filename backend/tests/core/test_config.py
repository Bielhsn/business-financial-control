import pytest

from app.core.config import Settings


def test_defaults_are_safe_for_local_development() -> None:
    settings = Settings(_env_file=None)

    assert settings.environment == "development"
    assert settings.mongodb_db_name == "business_financial_control"


def test_cors_origins_splits_comma_separated_values() -> None:
    settings = Settings(_env_file=None, cors_allowed_origins="http://a.com, http://b.com")

    assert settings.cors_origins == ["http://a.com", "http://b.com"]


def test_production_requires_non_default_secret_key() -> None:
    with pytest.raises(ValueError, match="SECRET_KEY"):
        Settings(_env_file=None, environment="production")
