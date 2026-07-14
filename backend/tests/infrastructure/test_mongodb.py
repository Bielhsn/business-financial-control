from unittest.mock import AsyncMock, patch

import pytest

import app.infrastructure.database.mongodb as mongodb_module

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
def _reset_client_singleton() -> None:
    mongodb_module._client = None
    yield
    mongodb_module._client = None


@patch("app.infrastructure.database.mongodb.AsyncMongoClient")
def test_get_client_returns_a_singleton(mock_client_cls: AsyncMock) -> None:
    first = mongodb_module.get_client()
    second = mongodb_module.get_client()

    assert first is second
    mock_client_cls.assert_called_once()


@patch("app.infrastructure.database.mongodb.init_beanie", new_callable=AsyncMock)
@patch("app.infrastructure.database.mongodb.AsyncMongoClient")
async def test_connect_to_mongo_initializes_beanie(
    mock_client_cls: AsyncMock, mock_init_beanie: AsyncMock
) -> None:
    await mongodb_module.connect_to_mongo()

    mock_init_beanie.assert_awaited_once()


@patch("app.infrastructure.database.mongodb.AsyncMongoClient")
async def test_close_mongo_connection_resets_the_singleton(mock_client_cls: AsyncMock) -> None:
    mock_instance = mock_client_cls.return_value
    mock_instance.close = AsyncMock()
    mongodb_module.get_client()

    await mongodb_module.close_mongo_connection()

    mock_instance.close.assert_awaited_once()
    assert mongodb_module._client is None


async def test_close_mongo_connection_is_a_no_op_when_never_connected() -> None:
    await mongodb_module.close_mongo_connection()

    assert mongodb_module._client is None


@patch("app.infrastructure.database.mongodb.AsyncMongoClient")
async def test_ping_database_returns_true_when_reachable(mock_client_cls: AsyncMock) -> None:
    mock_instance = mock_client_cls.return_value
    mock_instance.admin.command = AsyncMock(return_value={"ok": 1.0})

    assert await mongodb_module.ping_database() is True


@patch("app.infrastructure.database.mongodb.AsyncMongoClient")
async def test_ping_database_returns_false_when_unreachable(mock_client_cls: AsyncMock) -> None:
    mock_instance = mock_client_cls.return_value
    mock_instance.admin.command = AsyncMock(side_effect=RuntimeError("no connection"))

    assert await mongodb_module.ping_database() is False
