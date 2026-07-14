from app.core.logging import configure_logging, get_logger


def test_configure_logging_accepts_development_environment() -> None:
    configure_logging(log_level="DEBUG", environment="development")

    get_logger(__name__).info("test_event")


def test_configure_logging_accepts_production_environment() -> None:
    configure_logging(log_level="INFO", environment="production")

    get_logger(__name__).info("test_event")
